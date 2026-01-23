"""Data synchronization service - syncs API data to database."""
import logging
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import (
    Tournament,
    Player,
    ScoreSnapshot,
)
from app.services.api_client import SlashGolfAPIClient

logger = logging.getLogger(__name__)


def parse_mongodb_value(value: Any) -> Any:
    """Parse MongoDB format values to Python types."""
    if isinstance(value, dict):
        if "$numberInt" in value:
            return int(value["$numberInt"])
        elif "$numberLong" in value:
            return int(value["$numberLong"])
        elif "$date" in value:
            # Handle date format
            date_obj = value["$date"]
            if isinstance(date_obj, dict) and "$numberLong" in date_obj:
                timestamp_ms = int(date_obj["$numberLong"])
                return datetime.fromtimestamp(timestamp_ms / 1000)
            else:
                return datetime.fromtimestamp(int(date_obj) / 1000)
    return value


class DataSyncService:
    """Service for syncing Slash Golf API data to database."""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_client = SlashGolfAPIClient()
    
    def _parse_round_score(self, score_str: str) -> Optional[int]:
        """
        Parse currentRoundScore string to integer.
        
        Args:
            score_str: Score string like "-5", "+2", "E", or empty
            
        Returns:
            Integer score (negative for under par, positive for over par), or None if invalid
        """
        if not score_str or score_str == "":
            return None
        
        try:
            if score_str.startswith("-"):
                return -int(score_str[1:])
            elif score_str.startswith("+"):
                return int(score_str[1:])
            elif score_str == "E":
                return 0
            else:
                # Try to parse as integer directly
                return int(score_str)
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse score string: {score_str}")
            return None
    
    def sync_tournament(
        self,
        org_id: Optional[str] = None,
        tourn_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> Tournament:
        """
        Sync tournament data from API to database.
        
        Returns:
            Tournament model instance
        """
        # Fetch from API
        api_data = self.api_client.get_tournament(org_id, tourn_id, year)
        
        # Parse dates - handle MongoDB format or ISO string
        date_start = api_data["date"]["start"]
        date_end = api_data["date"]["end"]
        
        def parse_date(date_value):
            """Parse date from various formats."""
            if isinstance(date_value, str):
                # ISO string format
                return datetime.fromisoformat(date_value.replace("Z", "+00:00")).date()
            elif isinstance(date_value, dict) and "$date" in date_value:
                # MongoDB format: {"$date": {"$numberLong": "timestamp_ms"}}
                timestamp_ms = int(date_value["$date"].get("$numberLong", date_value["$date"]))
                return datetime.fromtimestamp(timestamp_ms / 1000).date()
            else:
                # Try to parse as string
                return datetime.fromisoformat(str(date_value).replace("Z", "+00:00")).date()
        
        start_date = parse_date(date_start)
        end_date = parse_date(date_end)
        
        # Check if tournament exists
        tournament = self.db.query(Tournament).filter(
            Tournament.tourn_id == api_data["tournId"],
            Tournament.year == int(api_data["year"])
        ).first()
        
        if tournament:
            # Update existing
            tournament.name = api_data["name"]
            tournament.start_date = start_date
            tournament.end_date = end_date
            tournament.status = api_data.get("status", "Unknown")
            tournament.current_round = parse_mongodb_value(api_data.get("currentRound", 1))
            # Store API data as JSON string
            tournament.api_data = json.loads(json.dumps(api_data, default=str))
            logger.info(f"Updated tournament: {tournament.name} ({tournament.year})")
        else:
            # Create new
            tournament = Tournament(
                year=int(api_data["year"]),
                tourn_id=api_data["tournId"],
                org_id=api_data["orgId"],
                name=api_data["name"],
                start_date=start_date,
                end_date=end_date,
                status=api_data.get("status", "Unknown"),
                current_round=parse_mongodb_value(api_data.get("currentRound", 1)),
                api_data=json.loads(json.dumps(api_data, default=str))  # Serialize to JSON
            )
            self.db.add(tournament)
            logger.info(f"Created tournament: {tournament.name} ({tournament.year})")
        
        self.db.commit()
        self.db.refresh(tournament)
        return tournament
    
    def sync_players_from_leaderboard(
        self,
        leaderboard_data: Dict[str, Any]
    ) -> List[Player]:
        """
        Sync players from leaderboard data.
        
        Args:
            leaderboard_data: Leaderboard data from API
            
        Returns:
            List of Player model instances
        """
        players = []
        leaderboard_rows = leaderboard_data.get("leaderboardRows", [])
        
        for row in leaderboard_rows:
            player_id = row.get("playerId")
            if not player_id:
                continue
            
            first_name = row.get("firstName", "")
            last_name = row.get("lastName", "")
            full_name = f"{first_name} {last_name}".strip()
            
            # Check if player exists
            player = self.db.query(Player).filter(
                Player.player_id == str(player_id)
            ).first()
            
            if player:
                # Update if name changed
                if player.full_name != full_name:
                    player.first_name = first_name
                    player.last_name = last_name
                    player.full_name = full_name
                    player.api_data = json.loads(json.dumps(row, default=str))
                    logger.debug(f"Updated player: {full_name}")
            else:
                # Create new
                player = Player(
                    player_id=str(player_id),
                    first_name=first_name,
                    last_name=last_name,
                    full_name=full_name,
                    api_data=json.loads(json.dumps(row, default=str))
                )
                self.db.add(player)
                logger.debug(f"Created player: {full_name}")
            
            players.append(player)
        
        try:
            self.db.commit()
            for player in players:
                self.db.refresh(player)
            logger.info(f"Synced {len(players)} players from leaderboard")
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error syncing players: {e}")
            raise
        
        return players
    
    def save_score_snapshot(
        self,
        tournament_id: int,
        round_id: int,
        leaderboard_data: Dict[str, Any],
        scorecard_data: Optional[Dict[str, Any]] = None
    ) -> ScoreSnapshot:
        """
        Save a snapshot of leaderboard/scorecard data.
        
        Args:
            tournament_id: Tournament ID
            round_id: Round number
            leaderboard_data: Leaderboard data from API
            scorecard_data: Optional scorecard data
            
        Returns:
            ScoreSnapshot model instance
        """
        snapshot = ScoreSnapshot(
            tournament_id=tournament_id,
            round_id=round_id,
            leaderboard_data=json.loads(json.dumps(leaderboard_data, default=str)),
            scorecard_data=json.loads(json.dumps(scorecard_data or {}, default=str))
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        logger.info(f"Saved score snapshot for tournament {tournament_id}, round {round_id}")
        return snapshot
    
    def sync_tournament_data(
        self,
        org_id: Optional[str] = None,
        tourn_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Sync all tournament data (tournament info, leaderboard, players).
        
        Returns:
            Dictionary with sync results
        """
        results = {
            "tournament": None,
            "players_synced": 0,
            "snapshot": None,
            "scorecards_fetched": 0,
            "errors": []
        }
        
        try:
            # Sync tournament
            tournament = self.sync_tournament(org_id, tourn_id, year)
            results["tournament"] = tournament
            
            # Get leaderboard
            leaderboard_data = self.api_client.get_leaderboard(org_id, tourn_id, year)
            
            # Sync players from leaderboard
            players = self.sync_players_from_leaderboard(leaderboard_data)
            results["players_synced"] = len(players)
            
            # Detect players who need scorecard fetching (2+ stroke improvement)
            current_round = tournament.current_round or 1
            players_to_fetch = self.detect_scorecard_changes(
                tournament_id=tournament.id,
                current_leaderboard=leaderboard_data,
                current_round=current_round
            )
            
            # Fetch scorecards for detected players
            scorecard_data = {}
            scorecards_fetched = 0
            for player_info in players_to_fetch:
                player_id = player_info["player_id"]
                try:
                    scorecards = self.api_client.get_scorecard(
                        player_id=player_id,
                        org_id=org_id,
                        tourn_id=tourn_id,
                        year=year
                    )
                    scorecard_data[player_id] = scorecards
                    scorecards_fetched += 1
                    logger.info(
                        f"Fetched scorecard for player {player_id} "
                        f"(improvement: {player_info['improvement']} strokes)"
                    )
                except Exception as e:
                    error_msg = f"Failed to fetch scorecard for player {player_id}: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
            
            # Save snapshot with scorecard data (if any)
            snapshot = self.save_score_snapshot(
                tournament_id=tournament.id,
                round_id=current_round,
                leaderboard_data=leaderboard_data,
                scorecard_data=scorecard_data if scorecard_data else None
            )
            results["snapshot"] = snapshot
            results["scorecards_fetched"] = scorecards_fetched
            
            logger.info(f"Successfully synced tournament {tournament.name}")
            
        except Exception as e:
            error_msg = f"Error syncing tournament data: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            self.db.rollback()
        
        return results
