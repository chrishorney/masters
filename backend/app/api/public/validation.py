"""Validation endpoints for checking sync status."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Tournament, ScoreSnapshot

router = APIRouter()


@router.get("/validation/api-raw")
async def get_raw_api_data(
    tournament_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Get raw API data from tournament to see what currentRound value is.
    Useful for debugging round detection issues.
    """
    # Get tournament
    if tournament_id:
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    else:
        tournament = db.query(Tournament).order_by(
            Tournament.year.desc(),
            Tournament.start_date.desc()
        ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="No tournament found")
    
    # Get raw API data stored in database
    api_data = tournament.api_data or {}
    
    return {
        "tournament_id": tournament.id,
        "tournament_name": tournament.name,
        "database_current_round": tournament.current_round,
        "api_data_currentRound": api_data.get("currentRound"),
        "api_data_currentRound_type": str(type(api_data.get("currentRound"))),
        "api_data_keys": list(api_data.keys()) if api_data else [],
        "full_api_data": api_data,  # Include full data for inspection
    }


@router.get("/validation/sync-status")
async def get_sync_status(
    tournament_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Validate sync status and current round information.
    
    Returns:
        Dictionary with tournament info, current round, and latest snapshot details
    """
    # Get tournament
    if tournament_id:
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    else:
        # Get most recent tournament
        tournament = db.query(Tournament).order_by(
            Tournament.year.desc(),
            Tournament.start_date.desc()
        ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="No tournament found")
    
    # Get latest snapshot for each round
    latest_snapshots = {}
    for round_id in range(1, 5):
        snapshot = db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament.id,
            ScoreSnapshot.round_id == round_id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        if snapshot:
            latest_snapshots[round_id] = {
                "snapshot_id": snapshot.id,
                "timestamp": snapshot.timestamp.isoformat(),
                "has_scorecard_data": bool(snapshot.scorecard_data and len(snapshot.scorecard_data) > 0),
                "scorecard_players": list(snapshot.scorecard_data.keys()) if snapshot.scorecard_data else []
            }
    
    # Get latest snapshot overall
    latest_snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament.id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    return {
        "tournament": {
            "id": tournament.id,
            "name": tournament.name,
            "year": tournament.year,
            "current_round": tournament.current_round,
            "status": tournament.status,
            "start_date": tournament.start_date.isoformat(),
            "end_date": tournament.end_date.isoformat(),
        },
        "latest_snapshot": {
            "id": latest_snapshot.id if latest_snapshot else None,
            "round_id": latest_snapshot.round_id if latest_snapshot else None,
            "timestamp": latest_snapshot.timestamp.isoformat() if latest_snapshot else None,
        } if latest_snapshot else None,
        "round_snapshots": latest_snapshots,
        "validation": {
            "current_round_matches_latest_snapshot": (
                latest_snapshot and 
                latest_snapshot.round_id == tournament.current_round
            ) if latest_snapshot else False,
            "has_snapshots": len(latest_snapshots) > 0,
            "rounds_with_snapshots": list(latest_snapshots.keys()),
        },
        "timestamp": datetime.now().isoformat()
    }
