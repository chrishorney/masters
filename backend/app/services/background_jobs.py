"""Background job service for automatic score updates."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Tournament, ScoreSnapshot
from app.services.data_sync import DataSyncService
from app.services.score_calculator import ScoreCalculatorService

logger = logging.getLogger(__name__)


class BackgroundJobService:
    """Service for running background jobs."""
    
    def __init__(self, db: Session):
        self.db = db
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, tournament_id: int, interval_seconds: int = 60):
        """
        Start background job to automatically sync and calculate scores.
        
        Args:
            tournament_id: Tournament ID to monitor
            interval_seconds: How often to check for updates (default: 60 seconds)
        """
        if self.running:
            logger.warning("Background job already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(
            self._run_loop(tournament_id, interval_seconds)
        )
        logger.info(f"Started background job for tournament {tournament_id}")
    
    async def stop(self):
        """Stop the background job."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped background job")
    
    async def _run_loop(self, tournament_id: int, interval_seconds: int):
        """Main loop for background job."""
        sync_service = DataSyncService(self.db)
        calculator = ScoreCalculatorService(self.db)
        
        while self.running:
            try:
                # Check if tournament is active
                tournament = self.db.query(Tournament).filter(
                    Tournament.id == tournament_id
                ).first()
                
                if not tournament:
                    logger.error(f"Tournament {tournament_id} not found")
                    break
                
                # Only run during active tournament days
                today = datetime.now().date()
                if tournament.start_date <= today <= tournament.end_date:
                    logger.info(f"Running background sync for tournament {tournament_id}")
                    
                    # Sync tournament data
                    try:
                        sync_results = sync_service.sync_tournament_data(
                            org_id=tournament.org_id,
                            tourn_id=tournament.tourn_id,
                            year=tournament.year
                        )
                        
                        if sync_results.get("errors"):
                            logger.warning(f"Sync completed with errors: {sync_results['errors']}")
                        
                        # Calculate scores for current round
                        calc_results = calculator.calculate_scores_for_tournament(
                            tournament_id=tournament_id,
                            round_id=tournament.current_round
                        )
                        
                        if calc_results.get("success"):
                            logger.info(
                                f"Calculated scores for {calc_results.get('entries_processed', 0)} entries"
                            )
                        else:
                            logger.warning(f"Score calculation failed: {calc_results.get('message')}")
                    
                    except Exception as e:
                        logger.error(f"Error in background job: {e}", exc_info=True)
                else:
                    logger.debug(f"Tournament not active today (start: {tournament.start_date}, end: {tournament.end_date})")
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in background job loop: {e}", exc_info=True)
                await asyncio.sleep(interval_seconds)
    
    async def run_once(self, tournament_id: int):
        """
        Run sync and calculation once (for manual trigger).
        
        Args:
            tournament_id: Tournament ID
        """
        sync_service = DataSyncService(self.db)
        calculator = ScoreCalculatorService(self.db)
        
        tournament = self.db.query(Tournament).filter(
            Tournament.id == tournament_id
        ).first()
        
        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")
        
        # Sync tournament data
        sync_results = sync_service.sync_tournament_data(
            org_id=tournament.org_id,
            tourn_id=tournament.tourn_id,
            year=tournament.year
        )
        
        # Calculate scores
        calc_results = calculator.calculate_scores_for_tournament(
            tournament_id=tournament_id,
            round_id=tournament.current_round
        )
        
        return {
            "sync": sync_results,
            "calculation": calc_results
        }
