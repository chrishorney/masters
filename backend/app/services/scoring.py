"""Scoring engine - calculates points based on tournament rules."""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import date
from sqlalchemy.orm import Session

from app.models import (
    Entry,
    DailyScore,
    BonusPoint,
    Tournament,
    Player,
)
from app.services.data_sync import parse_mongodb_value

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for calculating scores based on tournament rules."""
    
    # Scoring rules by round
    SCORING_RULES = {
        1: {  # Thursday
            "leader": 8,
            "top_5": 5,
            "top_10": 3,
            "top_25": 1,
        },
        2: {  # Friday
            "leader": 12,
            "top_5": 8,
            "top_10": 5,
            "top_25": 3,
            "made_cut": 1,
        },
        3: {  # Saturday
            "leader": 12,
            "top_5": 8,
            "top_10": 5,
            "top_25": 3,
            "made_cut": 1,
        },
        4: {  # Sunday
            "winner": 15,
            "leader": 12,  # If not winner
            "top_5": 8,
            "top_10": 5,
            "top_25": 3,
            "made_cut": 1,
        },
    }
    
    def __init__(self, db: Session):
        self.db = db
        # Initialize Discord service (will be None if disabled)
        try:
            from app.services.discord import get_discord_service
            self.discord_service = get_discord_service()
        except Exception as e:
            logger.debug(f"Discord service not available: {e}")
            self.discord_service = None
    
    def calculate_position_points(
        self,
        position: Optional[str],
        round_id: int,
        is_winner: bool = False,
        status: Optional[str] = None
    ) -> float:
        """
        Calculate points based on position and round.
        
        Args:
            position: Position string (e.g., "1", "T2", "5") or integer
            round_id: Round number (1-4)
            is_winner: Whether this is the tournament winner (Sunday only)
            
        Returns:
            Points earned
        """
        if not position:
            return 0.0
        
        # Handle both string and integer positions
        if isinstance(position, int):
            pos = position
        else:
            # Check if it's a status string (cut, wd, dq)
            if isinstance(position, str) and position.lower() in ["cut", "wd", "dq"]:
                return 0.0
            
            # Parse position (handle ties like "T2")
            try:
                pos_str = str(position).replace("T", "").strip()
                pos = int(pos_str)
            except (ValueError, AttributeError):
                return 0.0
        
        rules = self.SCORING_RULES.get(round_id, {})
        
        # Sunday special: winner gets 15 points
        if round_id == 4 and is_winner and pos == 1:
            return float(rules.get("winner", 15))
        
        # Check position ranges
        if pos == 1:
            return float(rules.get("leader", 0))
        elif pos <= 5:
            return float(rules.get("top_5", 0))
        elif pos <= 10:
            return float(rules.get("top_10", 0))
        elif pos <= 25:
            return float(rules.get("top_25", 0))
        elif round_id >= 2 and rules.get("made_cut"):
            # Made cut but outside top 25 (Friday-Sunday only)
            # Only award if player actually made the cut (status not "cut", "wd", or "dq")
            if status and status.lower() in ["cut", "wd", "dq"]:
                return 0.0
            return float(rules.get("made_cut", 0))
        
        return 0.0
    
    def get_player_position(
        self,
        leaderboard_data: Dict[str, Any],
        player_id: str
    ) -> Optional[str]:
        """Get player's position from leaderboard."""
        rows = leaderboard_data.get("leaderboardRows", [])
        for row in rows:
            if str(row.get("playerId")) == str(player_id):
                return row.get("position")
        return None
    
    def get_player_status(
        self,
        leaderboard_data: Dict[str, Any],
        player_id: str
    ) -> str:
        """Get player's status (complete, cut, wd, etc.)."""
        rows = leaderboard_data.get("leaderboardRows", [])
        for row in rows:
            if str(row.get("playerId")) == str(player_id):
                return row.get("status", "unknown")
        return "unknown"
    
    def calculate_daily_base_points(
        self,
        entry: Entry,
        leaderboard_data: Dict[str, Any],
        round_id: int,
        tournament: Tournament
    ) -> Dict[str, Any]:
        """
        Calculate base points for an entry for a given day.
        
        Returns:
            Dictionary with points breakdown
        """
        player_ids = [
            entry.player1_id,
            entry.player2_id,
            entry.player3_id,
            entry.player4_id,
            entry.player5_id,
            entry.player6_id,
        ]
        
        # Handle rebuys - use rebuy players for rounds 3-4 if applicable
        # For rounds 1-2, always use original players
        # For rounds 3-4, use rebuy players if they exist
        if round_id >= 3 and entry.rebuy_player_ids and entry.rebuy_original_player_ids:
            # Create mapping of original to rebuy
            rebuy_map = {}
            for orig_id, rebuy_id in zip(entry.rebuy_original_player_ids, entry.rebuy_player_ids):
                rebuy_map[str(orig_id)] = str(rebuy_id)
            
            # Replace original players with rebuy players
            player_ids = [rebuy_map.get(str(pid), str(pid)) for pid in player_ids]
        
        points_breakdown = {}
        total_points = 0.0
        
        # Check if this is the final round and determine winner
        is_final_round = (round_id == 4)
        winner_id = None
        if is_final_round:
            # Get winner from leaderboard (position 1, status complete)
            rows = leaderboard_data.get("leaderboardRows", [])
            for row in rows:
                if row.get("position") == "1" and row.get("status") == "complete":
                    winner_id = str(row.get("playerId"))
                    break
        
        for i, player_id in enumerate(player_ids, 1):
            position = self.get_player_position(leaderboard_data, player_id)
            status = self.get_player_status(leaderboard_data, player_id)
            
            # Skip if player didn't play this round (for rebuys)
            if round_id >= 3 and player_id in entry.rebuy_player_ids:
                # Check if original player should still count
                original_idx = entry.rebuy_original_player_ids.index(player_id) if player_id in entry.rebuy_original_player_ids else -1
                if original_idx >= 0:
                    original_player_id = [
                        entry.player1_id, entry.player2_id, entry.player3_id,
                        entry.player4_id, entry.player5_id, entry.player6_id
                    ][original_idx]
                    # Only count rebuy player, not original
                    pass
            
            is_winner = (is_final_round and str(player_id) == winner_id)
            points = self.calculate_position_points(position, round_id, is_winner, status)
            
            points_breakdown[f"player{i}"] = {
                "player_id": player_id,
                "position": position,
                "status": status,
                "points": points
            }
            total_points += points
        
        return {
            "total_points": total_points,
            "breakdown": points_breakdown
        }
    
    def calculate_bonus_points(
        self,
        entry: Entry,
        leaderboard_data: Dict[str, Any],
        scorecard_data: Dict[str, Any],
        round_id: int,
        tournament: Tournament
    ) -> List[Dict[str, Any]]:
        """
        Calculate bonus points for an entry.
        
        Returns:
            List of bonus point dictionaries
        """
        bonuses = []
        player_ids = [
            entry.player1_id,
            entry.player2_id,
            entry.player3_id,
            entry.player4_id,
            entry.player5_id,
            entry.player6_id,
        ]
        
        # Handle rebuys for rounds 3-4
        if round_id >= 3 and entry.rebuy_player_ids and entry.rebuy_original_player_ids:
            # Create mapping of original to rebuy
            rebuy_map = {}
            for orig_id, rebuy_id in zip(entry.rebuy_original_player_ids, entry.rebuy_player_ids):
                rebuy_map[str(orig_id)] = str(rebuy_id)
            
            # Replace original players with rebuy players
            player_ids = [rebuy_map.get(str(pid), str(pid)) for pid in player_ids]
        
        # Get manually added bonus points (GIR, Fairways) from database
        from app.models import BonusPoint
        manual_bonuses = self.db.query(BonusPoint).filter(
            BonusPoint.entry_id == entry.id,
            BonusPoint.round_id == round_id,
            BonusPoint.bonus_type.in_(["gir_leader", "fairways_leader"])
        ).all()
        
        # Add manual bonuses to the list
        for manual_bonus in manual_bonuses:
            # Check if this player is in the entry's lineup (original or rebuy)
            player_id_str = str(manual_bonus.player_id)
            if player_id_str in [str(pid) for pid in player_ids]:
                bonuses.append({
                    "player_id": player_id_str,
                    "bonus_type": manual_bonus.bonus_type,
                    "points": float(manual_bonus.points)
                })
        
        rows = leaderboard_data.get("leaderboardRows", [])
        
        # Find leaders in various categories
        # Note: API may not provide all stats, so we'll need to check what's available
        # For now, we'll implement what we can determine from the data
        
        # Low score of day
        low_score_player = None
        low_score_value = None
        for row in rows:
            if row.get("status") == "complete":
                current_round_score = row.get("currentRoundScore", "")
                # Parse score (e.g., "-5", "+2", "E")
                try:
                    if current_round_score.startswith("-"):
                        score = -int(current_round_score[1:])
                    elif current_round_score.startswith("+"):
                        score = int(current_round_score[1:])
                    elif current_round_score == "E":
                        score = 0
                    else:
                        continue
                    
                    if low_score_value is None or score < low_score_value:
                        low_score_value = score
                        low_score_player = str(row.get("playerId"))
                except (ValueError, AttributeError):
                    continue
        
        # Check each player for bonuses
        for player_id in player_ids:
            player_id_str = str(player_id)
            
            # Low score of day
            if low_score_player == player_id_str:
                bonuses.append({
                    "player_id": player_id_str,
                    "bonus_type": "low_score",
                    "points": 1.0
                })
            
            # Eagles, double eagles, hole in one from scorecard
            player_scorecards = scorecard_data.get(player_id_str, [])
            for scorecard in player_scorecards:
                if scorecard.get("roundId") == round_id:
                    holes = scorecard.get("holes", {})
                    for hole_num, hole_data in holes.items():
                        hole_score = hole_data.get("holeScore")
                        par = hole_data.get("par")
                        
                        if hole_score and par:
                            score_to_par = hole_score - par
                            
                            # Hole in one (always par 3)
                            if hole_score == 1 and par == 3:
                                bonuses.append({
                                    "player_id": player_id_str,
                                    "bonus_type": "hole_in_one",
                                    "points": 3.0,
                                    "hole": int(hole_num)
                                })
                            # Double eagle (3 under par)
                            elif score_to_par == -3:
                                bonuses.append({
                                    "player_id": player_id_str,
                                    "bonus_type": "double_eagle",
                                    "points": 3.0,
                                    "hole": int(hole_num)
                                })
                            # Eagle (2 under par)
                            elif score_to_par == -2:
                                bonuses.append({
                                    "player_id": player_id_str,
                                    "bonus_type": "eagle",
                                    "points": 2.0,
                                    "hole": int(hole_num)
                                })
        
        # All 6 make weekend bonus (Saturday only, round 3)
        # Only applies if all 6 ORIGINAL players made the cut (not rebuy players)
        if round_id == 3 and not entry.weekend_bonus_forfeited:
            # Use original 6 players, not rebuy players
            original_player_ids = [
                entry.player1_id,
                entry.player2_id,
                entry.player3_id,
                entry.player4_id,
                entry.player5_id,
                entry.player6_id,
            ]
            
            all_made_cut = True
            for player_id in original_player_ids:
                status = self.get_player_status(leaderboard_data, str(player_id))
                # Check if player made the cut (not cut, wd, or dq)
                if status in ["cut", "wd", "dq"]:
                    all_made_cut = False
                    break
            
            # Only award if all 6 original players made cut and bonus hasn't been earned yet
            if all_made_cut and not entry.weekend_bonus_earned:
                bonuses.append({
                    "player_id": None,  # Team bonus
                    "bonus_type": "all_make_cut",
                    "points": 5.0
                })
                entry.weekend_bonus_earned = True
        
        return bonuses
    
    def calculate_and_save_daily_score(
        self,
        entry: Entry,
        tournament: Tournament,
        leaderboard_data: Dict[str, Any],
        scorecard_data: Dict[str, Any],
        round_id: int,
        score_date: date
    ) -> DailyScore:
        """
        Calculate and save daily score for an entry.
        
        Returns:
            DailyScore model instance
        """
        # Calculate base points
        base_result = self.calculate_daily_base_points(
            entry, leaderboard_data, round_id, tournament
        )
        
        # Calculate bonus points
        bonuses = self.calculate_bonus_points(
            entry, leaderboard_data, scorecard_data, round_id, tournament
        )
        
        bonus_total = sum(b["points"] for b in bonuses)
        total_points = base_result["total_points"] + bonus_total
        
        # Check if score already exists
        existing_score = self.db.query(DailyScore).filter(
            DailyScore.entry_id == entry.id,
            DailyScore.round_id == round_id
        ).first()
        
        if existing_score:
            # Update existing
            existing_score.base_points = base_result["total_points"]
            existing_score.bonus_points = bonus_total
            existing_score.total_points = total_points
            existing_score.details = {
                "base_breakdown": base_result["breakdown"],
                "bonuses": bonuses
            }
            self.db.commit()
            self.db.refresh(existing_score)
            
            # Update bonus points records (but preserve manual ones like GIR/fairways)
            # Delete auto-calculated bonuses, keep manual ones
            from sqlalchemy import not_
            self.db.query(BonusPoint).filter(
                BonusPoint.entry_id == entry.id,
                BonusPoint.round_id == round_id,
                not_(BonusPoint.bonus_type.in_(["gir_leader", "fairways_leader"]))  # Keep manual bonuses
            ).delete()
            
            # Add auto-calculated bonuses (not manual ones)
            for bonus in bonuses:
                if bonus["bonus_type"] not in ["gir_leader", "fairways_leader"]:
                    # Check if it doesn't already exist (check by hole for eagle/albatross/hole-in-one)
                    query = self.db.query(BonusPoint).filter(
                        BonusPoint.entry_id == entry.id,
                        BonusPoint.round_id == round_id,
                        BonusPoint.bonus_type == bonus["bonus_type"],
                        BonusPoint.player_id == bonus.get("player_id")
                    )
                    
                    # For bonuses with holes, also check the hole number
                    if bonus.get("hole") is not None:
                        query = query.filter(BonusPoint.hole == bonus.get("hole"))
                    
                    existing = query.first()
                    
                    if not existing:
                        bonus_point = BonusPoint(
                            entry_id=entry.id,
                            round_id=round_id,
                            bonus_type=bonus["bonus_type"],
                            points=bonus["points"],
                            player_id=bonus.get("player_id"),
                            hole=bonus.get("hole")
                        )
                        self.db.add(bonus_point)
                        
                        # Send Discord notification for special bonuses (fire-and-forget, non-blocking)
                        self._notify_discord_bonus_async(
                            bonus=bonus,
                            round_id=round_id,
                            tournament=tournament
                        )
            
            self.db.commit()
            return existing_score
        else:
            # Create new
            daily_score = DailyScore(
                entry_id=entry.id,
                round_id=round_id,
                date=score_date,
                base_points=base_result["total_points"],
                bonus_points=bonus_total,
                total_points=total_points,
                details={
                    "base_breakdown": base_result["breakdown"],
                    "bonuses": bonuses
                }
            )
            self.db.add(daily_score)
            self.db.commit()
            self.db.refresh(daily_score)
            
            # Create bonus point records (only auto-calculated ones, manual ones already exist)
            for bonus in bonuses:
                if bonus["bonus_type"] not in ["gir_leader", "fairways_leader"]:
                    # Check if it doesn't already exist (check by hole for eagle/albatross/hole-in-one)
                    query = self.db.query(BonusPoint).filter(
                        BonusPoint.entry_id == entry.id,
                        BonusPoint.round_id == round_id,
                        BonusPoint.bonus_type == bonus["bonus_type"],
                        BonusPoint.player_id == bonus.get("player_id")
                    )
                    
                    # For bonuses with holes, also check the hole number
                    if bonus.get("hole") is not None:
                        query = query.filter(BonusPoint.hole == bonus.get("hole"))
                    
                    existing = query.first()
                    
                    if not existing:
                        bonus_point = BonusPoint(
                            entry_id=entry.id,
                            round_id=round_id,
                            bonus_type=bonus["bonus_type"],
                            points=bonus["points"],
                            player_id=bonus.get("player_id"),
                            hole=bonus.get("hole")
                        )
                        self.db.add(bonus_point)
                        
                        # Send Discord notification for special bonuses (fire-and-forget, non-blocking)
                        self._notify_discord_bonus_async(
                            bonus=bonus,
                            round_id=round_id,
                            tournament=tournament
                        )
            
            self.db.commit()
            return daily_score
    
    async def _notify_discord_bonus(
        self,
        bonus: Dict[str, Any],
        round_id: int,
        tournament: Tournament
    ):
        """
        Send Discord notification for bonus points (non-blocking, errors are logged but don't fail).
        
        Args:
            bonus: Bonus point dictionary
            round_id: Round number
            tournament: Tournament model
        """
        if not self.discord_service or not self.discord_service.enabled:
            return
        
        bonus_type = bonus.get("bonus_type")
        player_id = bonus.get("player_id")
        hole = bonus.get("hole")
        
        # Only notify for special bonuses (hole-in-one, eagles)
        if bonus_type not in ["hole_in_one", "double_eagle", "eagle"]:
            return
        
        if not player_id:
            return
        
        # Get player name
        player = self.db.query(Player).filter(Player.player_id == player_id).first()
        player_name = player.full_name if player else f"Player {player_id}"
        
        # Send appropriate notification
        if bonus_type == "hole_in_one":
            await self.discord_service.notify_hole_in_one(
                player_name=player_name,
                hole=hole or 0,
                round_id=round_id,
                tournament_name=tournament.name
            )
        elif bonus_type == "double_eagle":
            await self.discord_service.notify_double_eagle(
                player_name=player_name,
                hole=hole or 0,
                round_id=round_id,
                tournament_name=tournament.name
            )
        elif bonus_type == "eagle":
            await self.discord_service.notify_eagle(
                player_name=player_name,
                hole=hole or 0,
                round_id=round_id,
                tournament_name=tournament.name
            )