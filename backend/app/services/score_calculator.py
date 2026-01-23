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
            try:
                self._capture_ranking_snapshot(tournament_id, round_id)
            except Exception as e:
                # Log error but don't fail the calculation
                logger.error(f"Error capturing ranking snapshot: {e}", exc_info=True)
                results["errors"].append(f"Warning: Ranking snapshot failed: {e}")
        
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
