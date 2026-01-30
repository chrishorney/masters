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
    
    def detect_scorecard_changes(
        self,
        tournament_id: int,
        current_leaderboard: Dict[str, Any],
        current_round: int
    ) -> List[Dict[str, Any]]:
        """
        Compare current leaderboard to previous snapshot and detect players
        who improved by 2+ strokes (potential eagle/albatross/hole-in-one).
        
        Args:
            tournament_id: Tournament ID
            current_leaderboard: Current leaderboard data from API
            current_round: Current round number
            
        Returns:
            List of dictionaries with player_id, previous_score, current_score, and improvement
        """
        # Get previous snapshot for same round
        previous_snapshot = self.db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament_id,
            ScoreSnapshot.round_id == current_round
        ).order_by(ScoreSnapshot.timestamp.desc()).offset(1).first()
        
        if not previous_snapshot:
            # First snapshot for this round, no comparison possible
            logger.debug(f"No previous snapshot found for tournament {tournament_id}, round {current_round}")
            return []
        
        previous_leaderboard = previous_snapshot.leaderboard_data
        players_to_fetch = []
        
        # Build maps of player_id -> currentRoundScore
        current_scores = {}
        previous_scores = {}
        
        for row in current_leaderboard.get("leaderboardRows", []):
            player_id = str(row.get("playerId"))
            status = row.get("status", "").lower()
            score_str = row.get("currentRoundScore", "")
            
            # Skip if player hasn't started or is withdrawn/disqualified
            if status in ["wd", "dq", "cut"] or not score_str:
                continue
            
            current_scores[player_id] = self._parse_round_score(score_str)
        
        for row in previous_leaderboard.get("leaderboardRows", []):
            player_id = str(row.get("playerId"))
            score_str = row.get("currentRoundScore", "")
            if score_str:
                previous_scores[player_id] = self._parse_round_score(score_str)
        
        # Compare scores
        for player_id, current_score in current_scores.items():
            if current_score is None:
                continue
            
            previous_score = previous_scores.get(player_id)
            if previous_score is None:
                # Player just started, can't compare
                continue
            
            score_improvement = previous_score - current_score  # Negative = better score
            
            # If improved by 2+ strokes, fetch scorecard
            if score_improvement >= 2:
                players_to_fetch.append({
                    "player_id": player_id,
                    "previous_score": previous_score,
                    "current_score": current_score,
                    "improvement": score_improvement
                })
                logger.info(
                    f"Detected score improvement for player {player_id}: "
                    f"{previous_score} -> {current_score} (improvement: {score_improvement} strokes)"
                )
        
        logger.info(f"Detected {len(players_to_fetch)} players with 2+ stroke improvements")
        return players_to_fetch
    
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
            # Check if round changed (for Discord notifications)
            old_round = tournament.current_round
            
            # Update existing
            tournament.name = api_data["name"]
            tournament.start_date = start_date
            tournament.end_date = end_date
            tournament.status = api_data.get("status", "Unknown")
            
            # Get currentRound from API - log what we're getting
            raw_current_round = api_data.get("currentRound")
            logger.info(f"API returned currentRound: {raw_current_round} (type: {type(raw_current_round)})")
            parsed_round = parse_mongodb_value(raw_current_round) if raw_current_round is not None else 1
            tournament.current_round = parsed_round
            logger.info(f"Parsed current_round: {parsed_round} (was: {old_round})")
            
            # Store API data as JSON string
            tournament.api_data = json.loads(json.dumps(api_data, default=str))
            logger.info(f"Updated tournament: {tournament.name} ({tournament.year}) - Round {parsed_round}")
            
            # Notify Discord if round completed (round increased)
            if old_round and parsed_round > old_round and old_round >= 1:
                self._notify_discord_round_complete_async(tournament, old_round)
        else:
            # Create new
            # Get currentRound from API - log what we're getting
            raw_current_round = api_data.get("currentRound")
            logger.info(f"API returned currentRound: {raw_current_round} (type: {type(raw_current_round)})")
            parsed_round = parse_mongodb_value(raw_current_round) if raw_current_round is not None else 1
            logger.info(f"Parsed current_round: {parsed_round}")
            
            tournament = Tournament(
                year=int(api_data["year"]),
                tourn_id=api_data["tournId"],
                org_id=api_data["orgId"],
                name=api_data["name"],
                start_date=start_date,
                end_date=end_date,
                status=api_data.get("status", "Unknown"),
                current_round=parsed_round,
                api_data=json.loads(json.dumps(api_data, default=str))  # Serialize to JSON
            )
            self.db.add(tournament)
            logger.info(f"Created tournament: {tournament.name} ({tournament.year}) - Round {parsed_round}")
        
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
        # Refresh is not necessary - we already have the object with its ID after commit
        # Removing refresh to avoid unnecessary connection pool usage
        self.db.flush()  # Ensure the ID is available without a full refresh
        
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
                
                # Skip if we already have scorecard data for this player
                if player_id in scorecard_data:
                    continue
                
                try:
                    scorecards = self.api_client.get_scorecard(
                        player_id=player_id,
                        org_id=org_id,
                        tourn_id=tourn_id,
                        year=year
                    )
                    scorecard_data[player_id] = scorecards
                    scorecards_fetched += 1
                    reason = player_info.get("reason", "improvement")
                    improvement = player_info.get("improvement", 0)
                    if reason == "entry_player_backup":
                        logger.info(f"Fetched scorecard for entry player {player_id} (backup sync)")
                    else:
                        logger.info(
                            f"Fetched scorecard for player {player_id} "
                            f"(improvement: {improvement} strokes)"
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
            
            logger.info(
                f"Successfully synced tournament {tournament.name} - "
                f"Round {current_round} (from API: {tournament.current_round}), "
                f"Players: {len(players)}, "
                f"Scorecards fetched: {scorecards_fetched}"
            )
            
        except Exception as e:
            import traceback
            error_msg = f"Error syncing tournament data: {str(e) or type(e).__name__}"
            error_details = traceback.format_exc()
            logger.error(f"{error_msg}\n{error_details}")
            results["errors"].append(error_msg)
            results["error_details"] = error_details  # Include traceback for debugging
            self.db.rollback()
        
        return results
    
    def sync_round_data(
        self,
        tournament_id: int,
        round_id: int,
        org_id: Optional[str] = None,
        tourn_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Sync data for a specific round by fetching scorecards and reconstructing leaderboard.
        
        This is useful for:
        - Syncing historical rounds that weren't captured
        - Recovery if round data was lost
        - Testing with specific round data
        
        Args:
            tournament_id: Tournament ID in database
            round_id: Round number to sync (1-4)
            org_id: Organization ID (optional, will use tournament's if not provided)
            tourn_id: Tournament ID from API (optional, will use tournament's if not provided)
            year: Year (optional, will use tournament's if not provided)
            
        Returns:
            Dictionary with sync results
        """
        results = {
            "tournament": None,
            "round_id": round_id,
            "snapshot": None,
            "scorecards_fetched": 0,
            "players_processed": 0,
            "errors": []
        }
        
        try:
            # Get tournament
            tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
            if not tournament:
                raise ValueError(f"Tournament {tournament_id} not found")
            
            results["tournament"] = tournament
            
            # Use tournament's org_id, tourn_id, year if not provided
            sync_org_id = org_id or tournament.org_id
            sync_tourn_id = tourn_id or tournament.tourn_id
            sync_year = year or tournament.year
            
            # Get all players for this tournament (from leaderboard or existing players)
            leaderboard_data = self.api_client.get_leaderboard(sync_org_id, sync_tourn_id, sync_year)
            players = self.sync_players_from_leaderboard(leaderboard_data)
            
            # Fetch scorecards for ALL players (scorecards contain all rounds)
            scorecard_data = {}
            round_leaderboard_rows = []
            scorecards_fetched = 0
            rounds_found = 0
            rounds_matched = 0
            
            logger.info(f"Starting Round {round_id} sync for {len(players)} players")
            
            for player in players:
                player_id = player.player_id
                try:
                    scorecards = self.api_client.get_scorecard(
                        player_id=player_id,
                        org_id=sync_org_id,
                        tourn_id=sync_tourn_id,
                        year=sync_year
                    )
                    scorecard_data[player_id] = scorecards
                    scorecards_fetched += 1
                    
                    # Extract round-specific data from scorecard
                    round_data = None
                    scorecard_round_ids = []
                    for scorecard_round in scorecards:
                        rounds_found += 1
                        # Scorecard uses "roundId" not "round"
                        # Handle MongoDB format: {"$numberInt": "1"} or regular int/string
                        raw_round_id = scorecard_round.get("roundId")
                        if raw_round_id is not None:
                            # Parse MongoDB format if needed
                            scorecard_round_id = parse_mongodb_value(raw_round_id)
                            scorecard_round_ids.append(scorecard_round_id)
                            
                            # Convert to int for comparison (handles both "1" and 1)
                            try:
                                if int(scorecard_round_id) == round_id:
                                    round_data = scorecard_round
                                    rounds_matched += 1
                                    break
                            except (ValueError, TypeError):
                                # If conversion fails, try direct comparison
                                if scorecard_round_id == round_id:
                                    round_data = scorecard_round
                                    rounds_matched += 1
                                    break
                    
                    if not round_data and scorecard_round_ids:
                        logger.debug(f"Player {player_id}: Found rounds {scorecard_round_ids}, looking for {round_id}")
                    
                    if round_data:
                        # Reconstruct leaderboard row for this round
                        holes = round_data.get("holes", {})
                        total_shots = round_data.get("totalShots", 0)
                        current_round_score_str = round_data.get("currentRoundScore", "")
                        
                        # Parse score to par from string (e.g., "E", "-5", "+2")
                        score_to_par = self._parse_round_score(current_round_score_str)
                        if score_to_par is None:
                            # Calculate from holes if score string is invalid
                            total_par = sum(hole.get("par", 0) for hole in holes.values() if isinstance(hole, dict))
                            score_to_par = total_shots - total_par if total_par > 0 else 0
                        
                        # Calculate position (we'll need to sort by score later)
                        round_leaderboard_rows.append({
                            "playerId": player_id,
                            "firstName": player.first_name,
                            "lastName": player.last_name,
                            "currentRoundScore": current_round_score_str or self._format_score_to_par(score_to_par),
                            "totalScore": total_shots,
                            "scoreToPar": score_to_par,
                            "round": round_id,
                            "status": "active" if round_data.get("roundComplete", False) else "in_progress",
                            "holes": holes
                        })
                    
                except Exception as e:
                    error_msg = f"Failed to fetch scorecard for player {player_id}: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
            
            # Sort leaderboard by score (best first)
            round_leaderboard_rows.sort(key=lambda x: (x.get("scoreToPar", 999), x.get("totalScore", 999)))
            
            # Assign positions
            for idx, row in enumerate(round_leaderboard_rows):
                position = idx + 1
                # Handle ties (if score matches previous)
                if idx > 0 and round_leaderboard_rows[idx-1].get("scoreToPar") == row.get("scoreToPar"):
                    # Check if previous was a tie
                    prev_pos = round_leaderboard_rows[idx-1].get("position", position - 1)
                    row["position"] = prev_pos
                    row["positionDisplay"] = f"T{prev_pos}"
                else:
                    row["position"] = position
                    row["positionDisplay"] = str(position)
            
            # Reconstruct leaderboard structure
            round_leaderboard = {
                "leaderboardRows": round_leaderboard_rows,
                "round": round_id,
                "tournamentId": sync_tourn_id,
                "year": sync_year
            }
            
            # Save snapshot with round-specific data
            snapshot = self.save_score_snapshot(
                tournament_id=tournament_id,
                round_id=round_id,
                leaderboard_data=round_leaderboard,
                scorecard_data=scorecard_data
            )
            results["snapshot"] = snapshot
            results["scorecards_fetched"] = scorecards_fetched
            results["players_processed"] = len(round_leaderboard_rows)
            
            logger.info(
                f"Successfully synced Round {round_id} for tournament {tournament.name} - "
                f"Players processed: {len(players)}, "
                f"Scorecards fetched: {scorecards_fetched}, "
                f"Rounds found in scorecards: {rounds_found}, "
                f"Rounds matched (roundId={round_id}): {rounds_matched}, "
                f"Leaderboard rows created: {len(round_leaderboard_rows)}"
            )
            
            if len(round_leaderboard_rows) == 0:
                logger.warning(
                    f"No leaderboard rows created for Round {round_id}. "
                    f"This may indicate that no players have scorecard data for this round, "
                    f"or there's a mismatch in roundId values."
                )
            
        except Exception as e:
            import traceback
            error_msg = f"Error syncing round {round_id} data: {str(e) or type(e).__name__}"
            error_details = traceback.format_exc()
            logger.error(f"{error_msg}\n{error_details}")
            results["errors"].append(error_msg)
            results["error_details"] = error_details
            self.db.rollback()
        
        return results
    
    def _format_score_to_par(self, score_to_par: int) -> str:
        """Format score to par as string (e.g., -5, +2, E)."""
        if score_to_par == 0:
            return "E"
        elif score_to_par < 0:
            return str(score_to_par)
        else:
            return f"+{score_to_par}"
    
    def _notify_discord_round_complete_async(
        self,
        tournament: Tournament,
        completed_round: int
    ):
        """
        Notify Discord about round completion (fire-and-forget, non-blocking).
        
        Args:
            tournament: Tournament model
            completed_round: Round number that just completed
        """
        import asyncio
        
        async def notify():
            try:
                from app.services.discord import get_discord_service
                discord_service = get_discord_service()
                
                if not discord_service or not discord_service.enabled:
                    return
                
                # Get current leader
                from app.models import Entry, DailyScore
                entries = self.db.query(Entry).filter(
                    Entry.tournament_id == tournament.id
                ).all()
                
                if not entries:
                    return
                
                leaderboard_data = []
                for entry in entries:
                    daily_scores = self.db.query(DailyScore).filter(
                        DailyScore.entry_id == entry.id
                    ).order_by(DailyScore.round_id).all()
                    
                    total_points = sum(score.total_points for score in daily_scores)
                    leaderboard_data.append({
                        "entry_name": entry.participant.name if entry.participant else "Unknown",
                        "total_points": total_points
                    })
                
                leaderboard_data.sort(key=lambda x: x["total_points"], reverse=True)
                
                if leaderboard_data:
                    leader = leaderboard_data[0]
                    await discord_service.notify_round_complete(
                        round_id=completed_round,
                        leader_name=leader["entry_name"],
                        leader_points=leader["total_points"],
                        total_entries=len(entries),
                        tournament_name=tournament.name
                    )
                    
                    # Also send push notification
                    try:
                        from app.services.push_notifications import get_push_service
                        from app.models import PushSubscription
                        
                        push_service = get_push_service()
                        if push_service.enabled:
                            subscriptions = self.db.query(PushSubscription).filter(
                                PushSubscription.active == True
                            ).all()
                            
                            if subscriptions:
                                title = f"🏁 Round {completed_round} Complete!"
                                body = f"Round {completed_round} finished. {leader['entry_name']} leads with {leader['total_points']:.1f} points."
                                
                                for sub in subscriptions:
                                    push_service.send_notification(
                                        subscription=sub.subscription_data,
                                        title=title,
                                        body=body,
                                        url="/leaderboard"
                                    )
                    except Exception as push_error:
                        logger.warning(f"Push notification for round complete failed (non-critical): {push_error}")
            except Exception as e:
                logger.warning(f"Discord round completion notification failed (non-critical): {e}")
        
        # Fire-and-forget
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(notify())
            else:
                loop.run_until_complete(notify())
        except Exception as e:
            logger.debug(f"Could not schedule Discord notification: {e}")