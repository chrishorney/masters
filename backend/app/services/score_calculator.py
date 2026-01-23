"""Score calculator service - calculates scores for all entries."""
import logging
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models import Tournament, Entry, ScoreSnapshot, DailyScore, RankingSnapshot
from app.services.scoring import ScoringService
from app.services.api_client import SlashGolfAPIClient

logger = logging.getLogger(__name__)


class ScoreCalculatorService:
    """Service for calculating scores for all entries in a tournament."""
    
    def __init__(self, db: Session):
        self.db = db
        self.scoring_service = ScoringService(db)
        self.api_client = SlashGolfAPIClient()
    
    def calculate_scores_for_tournament(
        self,
        tournament_id: int,
        round_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate scores for all entries in a tournament.
        
        Args:
            tournament_id: Tournament ID
            round_id: Specific round to calculate (None = current round)
            
        Returns:
            Dictionary with calculation results
        """
        tournament = self.db.query(Tournament).filter(
            Tournament.id == tournament_id
        ).first()
        
        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")
        
        # Get current round if not specified
        if round_id is None:
            round_id = tournament.current_round or 1
        
        # Get latest score snapshot for this round
        snapshot = self.db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament_id,
            ScoreSnapshot.round_id == round_id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        if not snapshot:
            logger.warning(f"No score snapshot found for tournament {tournament_id}, round {round_id}")
            return {
                "success": False,
                "message": "No score snapshot found. Please sync tournament data first.",
                "entries_processed": 0
            }
        
        leaderboard_data = snapshot.leaderboard_data
        scorecard_data = snapshot.scorecard_data or {}
        
        # Get all entries for this tournament
        entries = self.db.query(Entry).filter(
            Entry.tournament_id == tournament_id
        ).all()
        
        results = {
            "success": True,
            "tournament_id": tournament_id,
            "round_id": round_id,
            "entries_processed": 0,
            "entries_updated": 0,
            "errors": []
        }
        
        # Calculate date for this round
        score_date = tournament.start_date
        if round_id > 1:
            # Approximate: add days for each round
            score_date = date.fromordinal(tournament.start_date.toordinal() + (round_id - 1))
        
        for entry in entries:
            try:
                daily_score = self.scoring_service.calculate_and_save_daily_score(
                    entry=entry,
                    tournament=tournament,
                    leaderboard_data=leaderboard_data,
                    scorecard_data=scorecard_data,
                    round_id=round_id,
                    score_date=score_date
                )
                results["entries_processed"] += 1
                results["entries_updated"] += 1
                logger.debug(f"Calculated score for entry {entry.id}: {daily_score.total_points} points")
            except Exception as e:
                error_msg = f"Error calculating score for entry {entry.id}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["entries_processed"] += 1
        
        logger.info(
            f"Calculated scores for {results['entries_updated']} entries "
            f"in tournament {tournament_id}, round {round_id}"
        )
        
        # Capture ranking snapshot after scores are calculated
        if results["success"] and results["entries_updated"] > 0:
            logger.info(f"Attempting to capture ranking snapshot for tournament {tournament_id}, round {round_id}")
            try:
                snapshots_created = self._capture_ranking_snapshot(tournament_id, round_id)
                logger.info(f"Successfully captured {snapshots_created} ranking snapshots")
            except Exception as e:
                # Log error but don't fail the calculation
                logger.error(f"Error capturing ranking snapshot: {e}", exc_info=True)
                results["errors"].append(f"Warning: Ranking snapshot failed: {e}")
        else:
            logger.debug(
                f"Skipping ranking snapshot capture: success={results.get('success')}, "
                f"entries_updated={results.get('entries_updated')}"
            )
        
        return results
    
    def calculate_all_rounds(
        self,
        tournament_id: int
    ) -> Dict[str, Any]:
        """
        Calculate scores for all completed rounds.
        
        Args:
            tournament_id: Tournament ID
            
        Returns:
            Dictionary with results for each round
        """
        tournament = self.db.query(Tournament).filter(
            Tournament.id == tournament_id
        ).first()
        
        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")
        
        current_round = tournament.current_round or 1
        results = {
            "tournament_id": tournament_id,
            "rounds_processed": [],
            "total_entries_processed": 0,
            "errors": []
        }
        
        # Calculate for each completed round
        for round_id in range(1, current_round + 1):
            try:
                round_result = self.calculate_scores_for_tournament(
                    tournament_id, round_id
                )
                results["rounds_processed"].append({
                    "round_id": round_id,
                    "entries_processed": round_result.get("entries_processed", 0),
                    "entries_updated": round_result.get("entries_updated", 0),
                })
                results["total_entries_processed"] += round_result.get("entries_processed", 0)
            except Exception as e:
                error_msg = f"Error calculating round {round_id}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results
    
    def _capture_ranking_snapshot(
        self,
        tournament_id: int,
        round_id: int
    ) -> int:
        """
        Capture a snapshot of current rankings for all entries.
        
        This creates RankingSnapshot records for each entry showing their
        position and total points at this moment in time.
        
        Args:
            tournament_id: Tournament ID
            round_id: Round number
            
        Returns:
            Number of snapshots created
        """
        # Get all entries for this tournament
        entries = self.db.query(Entry).filter(
            Entry.tournament_id == tournament_id
        ).all()
        
        if not entries:
            logger.warning(f"No entries found for tournament {tournament_id}")
            return 0
        
        # Calculate current rankings (same logic as get_leaderboard)
        leaderboard_data = []
        
        for entry in entries:
            # Get all daily scores for this entry
            daily_scores = self.db.query(DailyScore).filter(
                DailyScore.entry_id == entry.id
            ).order_by(DailyScore.round_id).all()
            
            total_points = sum(score.total_points for score in daily_scores)
            
            leaderboard_data.append({
                "entry_id": entry.id,
                "total_points": total_points
            })
        
        # Sort by total points descending
        leaderboard_data.sort(key=lambda x: x["total_points"], reverse=True)
        
        # Determine leader's points
        leader_points = leaderboard_data[0]["total_points"] if leaderboard_data else 0
        
        # Create ranking snapshots
        snapshots_created = 0
        for position, entry_data in enumerate(leaderboard_data, start=1):
            entry_id = entry_data["entry_id"]
            total_points = entry_data["total_points"]
            points_behind = leader_points - total_points if leader_points > 0 else 0
            
            # Always create a new snapshot to track position changes over time
            # Even if points are the same, position might have changed due to other entries
            # This allows us to see the full history of position changes
            should_create = True
            
            if should_create:
                snapshot = RankingSnapshot(
                    tournament_id=tournament_id,
                    entry_id=entry_id,
                    round_id=round_id,
                    position=position,
                    total_points=total_points,
                    points_behind_leader=points_behind,
                    timestamp=datetime.utcnow()
                )
                self.db.add(snapshot)
                snapshots_created += 1
        
        if snapshots_created > 0:
            self.db.commit()
            logger.info(
                f"Created {snapshots_created} ranking snapshots for tournament {tournament_id}, round {round_id}"
            )
        
        return snapshots_created