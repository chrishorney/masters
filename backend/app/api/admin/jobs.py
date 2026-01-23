"""Admin endpoints for background jobs."""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Tournament, ScoreSnapshot
from app.services.background_jobs import BackgroundJobService

logger = logging.getLogger(__name__)

router = APIRouter()

# Global job service instance (in production, use proper job queue like Celery)
_job_services: dict[int, BackgroundJobService] = {}


@router.post("/jobs/start")
async def start_background_job(
    tournament_id: int = Query(..., description="Tournament ID"),
    interval_seconds: int = Query(60, description="Update interval in seconds"),
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
    
    # Check if job already running
    if tournament_id in _job_services:
        return {
            "message": "Background job already running",
            "tournament_id": tournament_id,
            "status": "running"
        }
    
    # Create and start job service
    job_service = BackgroundJobService(db)
    await job_service.start(tournament_id, interval_seconds, start_hour, stop_hour)
    _job_services[tournament_id] = job_service
    
    return {
        "message": "Background job started",
        "tournament_id": tournament_id,
        "interval_seconds": interval_seconds,
        "start_hour": start_hour,
        "stop_hour": stop_hour,
        "active_hours": f"{start_hour:02d}:00 - {stop_hour:02d}:59",
        "status": "started"
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
        raise HTTPException(status_code=404, detail="Background job not found")
    
    job_service = _job_services[tournament_id]
    await job_service.stop()
    # Remove from running jobs - this prevents any automatic restart
    del _job_services[tournament_id]
    
    return {
        "message": "Background job stopped permanently. It will not restart automatically.",
        "tournament_id": tournament_id,
        "status": "stopped"
    }


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
    """
    is_in_dict = tournament_id in _job_services
    
    # Check if task is actually running (not just in dictionary)
    is_actually_running = False
    if is_in_dict:
        job_service = _job_services[tournament_id]
        # Check if service thinks it's running AND task exists and is not done
        if hasattr(job_service, 'running') and job_service.running:
            if hasattr(job_service, '_task') and job_service._task is not None:
                # Check if task is done or cancelled
                if not job_service._task.done():
                    is_actually_running = True
                else:
                    # Task is done but service thinks it's running - clean up
                    logger.warning(f"Job service for tournament {tournament_id} has completed task but running flag is True. Cleaning up.")
                    job_service.running = False
                    if tournament_id in _job_services:
                        del _job_services[tournament_id]
            else:
                # No task but service thinks it's running - clean up
                logger.warning(f"Job service for tournament {tournament_id} has no task but running flag is True. Cleaning up.")
                job_service.running = False
                if tournament_id in _job_services:
                    del _job_services[tournament_id]
    
    result = {
        "tournament_id": tournament_id,
        "running": is_actually_running,
        "status": "running" if is_actually_running else "stopped"
    }
    
    # Add time info if running
    if is_actually_running and is_in_dict:
        job_service = _job_services[tournament_id]
        result["start_hour"] = getattr(job_service, 'start_hour', 6)
        result["stop_hour"] = getattr(job_service, 'stop_hour', 23)
        result["active_hours"] = f"{result['start_hour']:02d}:00 - {result['stop_hour']:02d}:59"
    
    # Get last sync timestamp from most recent ScoreSnapshot
    last_snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    if last_snapshot:
        result["last_sync_timestamp"] = last_snapshot.timestamp.isoformat()
        result["last_sync_round"] = last_snapshot.round_id
        
        # Calculate time since last sync
        time_diff = datetime.now() - last_snapshot.timestamp
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
