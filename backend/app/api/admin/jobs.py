"""Admin endpoints for background jobs."""
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Tournament, ScoreSnapshot
from app.services.background_jobs import BackgroundJobService

logger = logging.getLogger(__name__)

# Central Time zone
CENTRAL_TZ = ZoneInfo("America/Chicago")

router = APIRouter()

# Global job service instance (in production, use proper job queue like Celery)
# NOTE: This is in-memory and will be lost on server restart
_job_services: dict[int, BackgroundJobService] = {}


@router.post("/jobs/start")
async def start_background_job(
    tournament_id: int = Query(..., description="Tournament ID"),
    interval_seconds: int = Query(300, description="Update interval in seconds (default: 300 = 5 minutes)"),
    start_hour: int = Query(6, description="Hour to start syncing (0-23, default: 6 = 6 AM)"),
    stop_hour: int = Query(23, description="Hour to stop syncing (0-23, default: 23 = 11 PM)"),
    db: Session = Depends(get_db)
):
    """Start background job for automatic score updates."""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Validate hours
    if not (0 <= start_hour <= 23) or not (0 <= stop_hour <= 23):
        raise HTTPException(status_code=400, detail="Hours must be between 0 and 23")
    
    # Validate interval
    if interval_seconds < 60:
        raise HTTPException(status_code=400, detail="Interval must be at least 60 seconds")
    
    # Check if job already running - stop it first if it exists
    if tournament_id in _job_services:
        existing_job = _job_services[tournament_id]
        if existing_job.running:
            logger.info(f"Stopping existing job for tournament {tournament_id} before starting new one")
            await existing_job.stop()
        del _job_services[tournament_id]
    
    # Create and start job service
    # NOTE: We pass the db session, but the job will create its own sessions
    job_service = BackgroundJobService(db)
    await job_service.start(tournament_id, interval_seconds, start_hour, stop_hour)
    _job_services[tournament_id] = job_service
    
    logger.info(
        f"Background job started for tournament {tournament_id}: "
        f"interval={interval_seconds}s, hours={start_hour:02d}:00-{stop_hour:02d}:59"
    )
    
    return {
        "message": "Background job started",
        "tournament_id": tournament_id,
        "interval_seconds": interval_seconds,
        "start_hour": start_hour,
        "stop_hour": stop_hour,
        "active_hours": f"{start_hour:02d}:00 - {stop_hour:02d}:59",
        "status": "started",
        "warning": "Job is in-memory and will be lost on server restart. Use a proper job queue (like Celery) for production."
    }


@router.post("/jobs/stop")
async def stop_background_job(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """
    Stop background job.
    
    IMPORTANT: This is a hard override. Once stopped, the job will NOT automatically
    restart, even when active hours begin again. The job must be manually started
    again via the /jobs/start endpoint.
    """
    if tournament_id not in _job_services:
        # Job might have already stopped or doesn't exist
        # Check if it's actually running by checking the status
        logger.warning(f"Job service not found in dictionary for tournament {tournament_id}")
        return {
            "message": "Background job is not running or has already stopped.",
            "tournament_id": tournament_id,
            "status": "stopped"
        }
    
    job_service = _job_services[tournament_id]
    
    try:
        # Check if job is actually running before trying to stop
        if not job_service.running:
            logger.info(f"Job for tournament {tournament_id} is already stopped")
            # Clean up anyway
            del _job_services[tournament_id]
            return {
                "message": "Background job was already stopped.",
                "tournament_id": tournament_id,
                "status": "stopped"
            }
        
        # Stop the job
        await job_service.stop()
        
        # Remove from running jobs - this prevents any automatic restart
        if tournament_id in _job_services:
            del _job_services[tournament_id]
        
        logger.info(f"Background job stopped for tournament {tournament_id}")
        
        return {
            "message": "Background job stopped permanently. It will not restart automatically.",
            "tournament_id": tournament_id,
            "status": "stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping background job for tournament {tournament_id}: {e}", exc_info=True)
        
        # Try to clean up even if stop() failed
        if tournament_id in _job_services:
            try:
                job_service.running = False
                if hasattr(job_service, '_task') and job_service._task:
                    job_service._task.cancel()
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
            finally:
                del _job_services[tournament_id]
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop background job: {str(e)}"
        )


@router.get("/jobs/status")
async def get_job_status(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """
    Get background job status and last sync information.
    
    Returns:
        - running: Whether the background job is currently running
        - status: "running" or "stopped"
        - last_sync_timestamp: ISO timestamp of the most recent sync (if any)
        - last_sync_round: Round number of the most recent sync (if any)
        - time_since_last_sync: Human-readable time since last sync (if any)
        - debug_info: Additional debugging information
    """
    is_in_dict = tournament_id in _job_services
    
    # Check if task is actually running (not just in dictionary)
    is_actually_running = False
    task_status = None
    if is_in_dict:
        job_service = _job_services[tournament_id]
        # Check if service thinks it's running AND task exists and is not done
        if hasattr(job_service, 'running') and job_service.running:
            if hasattr(job_service, '_task') and job_service._task is not None:
                # Check if task is done or cancelled
                if not job_service._task.done():
                    is_actually_running = True
                    task_status = "running"
                else:
                    # Task is done but service thinks it's running - clean up
                    task_status = f"done (exception: {job_service._task.exception()})" if job_service._task.exception() else "done"
                    logger.warning(f"Job service for tournament {tournament_id} has completed task but running flag is True. Cleaning up.")
                    job_service.running = False
                    if tournament_id in _job_services:
                        del _job_services[tournament_id]
            else:
                # No task but service thinks it's running - clean up
                task_status = "no_task"
                logger.warning(f"Job service for tournament {tournament_id} has no task but running flag is True. Cleaning up.")
                job_service.running = False
                if tournament_id in _job_services:
                    del _job_services[tournament_id]
        else:
            task_status = "not_running"
    
    # Get tournament info for debugging (using Central Time)
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    now_utc = datetime.now(timezone.utc)
    now_ct = now_utc.astimezone(CENTRAL_TZ)
    current_hour = now_ct.hour
    
    result = {
        "tournament_id": tournament_id,
        "running": is_actually_running,
        "status": "running" if is_actually_running else "stopped",
        "debug_info": {
            "in_job_services_dict": is_in_dict,
            "task_status": task_status,
            "current_hour": current_hour,
            "current_hour_timezone": "CT",
            "current_time": now_ct.isoformat(),
            "current_time_utc": now_utc.isoformat(),
        }
    }
    
    # Add time info if running
    if is_actually_running and is_in_dict:
        job_service = _job_services[tournament_id]
        result["start_hour"] = getattr(job_service, 'start_hour', 6)
        result["stop_hour"] = getattr(job_service, 'stop_hour', 23)
        result["active_hours"] = f"{result['start_hour']:02d}:00 - {result['stop_hour']:02d}:59"
        
        # Check if within active hours
        if hasattr(job_service, '_is_within_active_hours'):
            within_hours = job_service._is_within_active_hours(
                current_hour, 
                result["start_hour"], 
                result["stop_hour"]
            )
            result["debug_info"]["within_active_hours"] = within_hours
        
        # Check if tournament is active
        if tournament:
            today = now.date()
            is_active = tournament.start_date <= today <= tournament.end_date
            result["debug_info"]["tournament_active"] = is_active
            result["debug_info"]["tournament_start_date"] = tournament.start_date.isoformat()
            result["debug_info"]["tournament_end_date"] = tournament.end_date.isoformat()
            result["debug_info"]["tournament_current_round"] = tournament.current_round
    
    # Get last sync timestamp from most recent ScoreSnapshot
    last_snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    if last_snapshot:
        # Ensure timestamp is in UTC for proper timezone conversion on frontend
        timestamp = last_snapshot.timestamp
        if timestamp.tzinfo is None:
            # Make it timezone-aware as UTC (database typically stores UTC)
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        result["last_sync_timestamp"] = timestamp.isoformat()
        result["last_sync_round"] = last_snapshot.round_id
        
        # Calculate time since last sync (use UTC for both)
        now_utc = datetime.now(timezone.utc)
        if last_snapshot.timestamp.tzinfo is None:
            snapshot_utc = last_snapshot.timestamp.replace(tzinfo=timezone.utc)
        else:
            snapshot_utc = last_snapshot.timestamp
        time_diff = now_utc - snapshot_utc
        total_seconds = int(time_diff.total_seconds())
        
        if total_seconds < 60:
            result["time_since_last_sync"] = f"{total_seconds} seconds ago"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            result["time_since_last_sync"] = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            result["time_since_last_sync"] = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = total_seconds // 86400
            result["time_since_last_sync"] = f"{days} day{'s' if days != 1 else ''} ago"
    else:
        result["last_sync_timestamp"] = None
        result["last_sync_round"] = None
        result["time_since_last_sync"] = "Never"
    
    return result


@router.post("/jobs/run-once")
async def run_job_once(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """Run sync and calculation once (manual trigger)."""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    job_service = BackgroundJobService(db)
    results = await job_service.run_once(tournament_id)
    
    return {
        "message": "Job executed successfully",
        "tournament_id": tournament_id,
        "results": results
    }
