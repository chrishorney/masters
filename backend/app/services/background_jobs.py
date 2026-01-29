"""Background job service for automatic score updates."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from app.models import Tournament, ScoreSnapshot
from app.services.data_sync import DataSyncService
from app.services.score_calculator import ScoreCalculatorService

logger = logging.getLogger(__name__)

# Central Time zone
CENTRAL_TZ = ZoneInfo("America/Chicago")


class BackgroundJobService:
    """Service for running background jobs."""
    
    def __init__(self, db: Session):
        self.db = db
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(
        self, 
        tournament_id: int, 
        interval_seconds: int = 60,
        start_hour: int = 6,
        stop_hour: int = 23
    ):
        """
        Start background job to automatically sync and calculate scores.
        
        Args:
            tournament_id: Tournament ID to monitor
            interval_seconds: How often to check for updates (default: 60 seconds)
            start_hour: Hour of day to start syncing (0-23, default: 6 = 6 AM)
            stop_hour: Hour of day to stop syncing (0-23, default: 23 = 11 PM)
        """
        if self.running:
            logger.warning("Background job already running")
            return
        
        self.running = True
        self.start_hour = start_hour
        self.stop_hour = stop_hour
        self._task = asyncio.create_task(
            self._run_loop(tournament_id, interval_seconds, start_hour, stop_hour)
        )
        logger.info(
            f"Started background job for tournament {tournament_id} "
            f"(active hours: {start_hour:02d}:00 - {stop_hour:02d}:59)"
        )
    
    async def stop(self):
        """
        Stop the background job.
        
        This is a hard stop - the job will not restart automatically.
        It must be explicitly started again via the start() method.
        """
        self.running = False
        
        if self._task:
            try:
                # Check if task is already done
                if self._task.done():
                    logger.debug("Task was already done, no need to cancel")
                else:
                    # Cancel the task
                    self._task.cancel()
                    try:
                        # Wait for cancellation to complete (with timeout)
                        await asyncio.wait_for(self._task, timeout=5.0)
                    except asyncio.CancelledError:
                        logger.debug("Task cancelled successfully")
                    except asyncio.TimeoutError:
                        logger.warning("Task cancellation timed out, but continuing with stop")
                    except Exception as e:
                        logger.warning(f"Exception while waiting for task cancellation: {e}")
            except Exception as e:
                logger.error(f"Error during task cancellation: {e}", exc_info=True)
                # Continue anyway - we've set running=False
        
        logger.info("Background job stopped permanently (will not auto-restart)")
    
    def _is_within_active_hours(self, current_hour: int, start_hour: int, stop_hour: int) -> bool:
        """
        Check if current hour is within active sync hours.
        
        Handles cases where stop_hour < start_hour (e.g., 22-6 means 10 PM to 6 AM).
        """
        if start_hour <= stop_hour:
            # Normal case: start_hour <= stop_hour (e.g., 6-23 means 6 AM to 11 PM)
            return start_hour <= current_hour <= stop_hour
        else:
            # Wraps around midnight (e.g., 22-6 means 10 PM to 6 AM)
            return current_hour >= start_hour or current_hour <= stop_hour
    
    def _is_connection_pool_error(self, error: Exception) -> bool:
        """Check if error is a connection pool exhaustion error."""
        error_str = str(error).lower()
        return (
            "maxclientsinsessionmode" in error_str or
            "max clients reached" in error_str or
            "connection pool" in error_str or
            "pool_size" in error_str
        )
    
    async def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 2.0):
        """
        Retry a function with exponential backoff, especially for connection pool errors.
        
        Args:
            func: Async function to retry
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds for exponential backoff
        """
        for attempt in range(max_retries):
            try:
                return await func()
            except (OperationalError, Exception) as e:
                if attempt == max_retries - 1:
                    # Last attempt, re-raise
                    raise
                
                # Check if it's a connection pool error
                if self._is_connection_pool_error(e):
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Connection pool error (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    # Not a connection pool error, re-raise immediately
                    raise

    async def _run_loop(
        self, 
        tournament_id: int, 
        interval_seconds: int,
        start_hour: int,
        stop_hour: int
    ):
        """Main loop for background job."""
        # Don't reuse the same DB session - create new ones for each operation
        # to avoid session expiration issues
        
        try:
            consecutive_errors = 0
            max_consecutive_errors = 5
            
            while self.running:
                try:
                    # Create fresh database session for this iteration
                    from app.database import SessionLocal
                    db = SessionLocal()
                    
                    try:
                        # Check if tournament is active
                        tournament = db.query(Tournament).filter(
                            Tournament.id == tournament_id
                        ).first()
                        
                        if not tournament:
                            logger.error(f"Tournament {tournament_id} not found")
                            consecutive_errors += 1
                            if consecutive_errors >= max_consecutive_errors:
                                logger.error(f"Too many consecutive errors ({consecutive_errors}). Stopping job.")
                                self.running = False
                                break
                            await asyncio.sleep(interval_seconds)
                            continue
                        
                        # Reset error counter on success
                        consecutive_errors = 0
                    
                        # Check if within active hours (using Central Time)
                        now_utc = datetime.now(timezone.utc)
                        now_ct = now_utc.astimezone(CENTRAL_TZ)
                        current_hour = now_ct.hour
                        
                        if not self._is_within_active_hours(current_hour, start_hour, stop_hour):
                            logger.debug(
                                f"Skipping sync - outside active hours "
                                f"(current: {current_hour:02d}:00 CT, active: {start_hour:02d}:00-{stop_hour:02d}:59 CT)"
                            )
                            db.close()
                            await asyncio.sleep(interval_seconds)
                            continue
                        
                        # Only run during active tournament days (using Central Time date)
                        today = now_ct.date()
                        if tournament.start_date <= today <= tournament.end_date:
                            logger.info(
                                f"Running background sync for tournament {tournament_id} "
                                f"(Round {tournament.current_round}, {now_ct.strftime('%Y-%m-%d %H:%M:%S')} CT)"
                            )
                            
                            # Close the outer session before starting sync/calc to free up connections
                            db.close()
                            
                            # Sync tournament data with retry logic for connection pool errors
                            try:
                                async def sync_and_calculate():
                                    # Create a fresh session for this attempt
                                    from app.database import SessionLocal
                                    retry_db = SessionLocal()
                                    
                                    try:
                                        sync_service = DataSyncService(retry_db)
                                        calculator = ScoreCalculatorService(retry_db)
                                        
                                        logger.info(f"Syncing tournament data for {tournament.name}...")
                                        sync_results = sync_service.sync_tournament_data(
                                            org_id=tournament.org_id,
                                            tourn_id=tournament.tourn_id,
                                            year=tournament.year
                                        )
                                        
                                        if sync_results.get("errors"):
                                            logger.warning(f"Sync completed with errors: {sync_results['errors']}")
                                        else:
                                            logger.info(f"Sync completed successfully. Players: {sync_results.get('players_synced', 0)}, Scorecards: {sync_results.get('scorecards_fetched', 0)}")
                                        
                                        # Calculate scores for current round
                                        logger.info(f"Calculating scores for Round {tournament.current_round}...")
                                        calc_results = calculator.calculate_scores_for_tournament(
                                            tournament_id=tournament_id,
                                            round_id=tournament.current_round
                                        )
                                        
                                        if calc_results.get("success"):
                                            logger.info(
                                                f"Calculated scores for {calc_results.get('entries_processed', 0)} entries "
                                                f"(updated: {calc_results.get('entries_updated', 0)})"
                                            )
                                        else:
                                            logger.warning(f"Score calculation failed: {calc_results.get('message')}")
                                        
                                        return sync_results, calc_results
                                    finally:
                                        # Always close the retry session
                                        retry_db.close()
                                
                                # Retry with exponential backoff for connection pool errors
                                await self._retry_with_backoff(sync_and_calculate, max_retries=3, base_delay=2.0)
                            
                            except Exception as e:
                                error_msg = str(e)
                                if self._is_connection_pool_error(e):
                                    logger.error(
                                        f"Connection pool exhausted after retries. "
                                        f"This may indicate too many concurrent connections. "
                                        f"Error: {error_msg}"
                                    )
                                else:
                                    logger.error(f"Error in background job sync/calc: {e}", exc_info=True)
                                
                                consecutive_errors += 1
                                if consecutive_errors >= max_consecutive_errors:
                                    logger.error(f"Too many consecutive errors ({consecutive_errors}). Stopping job.")
                                    self.running = False
                                    break
                        else:
                            logger.info(
                                f"Tournament not active today "
                                f"(start: {tournament.start_date}, end: {tournament.end_date}, today: {today})"
                            )
                    
                    finally:
                        # Always close the database session
                        # Use try/except in case session was already closed
                        try:
                            db.close()
                        except Exception:
                            pass  # Session may already be closed
                    
                    # Wait for next interval
                    await asyncio.sleep(interval_seconds)
                
                except asyncio.CancelledError:
                    logger.info(f"Background job for tournament {tournament_id} was cancelled")
                    self.running = False
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in background job loop iteration: {e}", exc_info=True)
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Too many consecutive errors ({consecutive_errors}). Stopping job.")
                        self.running = False
                        break
                    # Continue running even if there's an error, but wait before retrying
                    await asyncio.sleep(interval_seconds)
        except Exception as e:
            logger.error(f"Critical error in background job loop: {e}", exc_info=True)
            self.running = False
        finally:
            # Ensure running flag is set to False when loop exits
            self.running = False
            logger.info(f"Background job loop for tournament {tournament_id} has stopped")
    
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
