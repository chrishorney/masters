"""Public tournament endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Tournament
from app.services.data_sync import DataSyncService

router = APIRouter()


@router.get("/tournament/current")
async def get_current_tournament(
    db: Session = Depends(get_db)
):
    """Get current tournament information."""
    # Get the most recent active tournament
    tournament = db.query(Tournament).order_by(
        Tournament.year.desc(),
        Tournament.start_date.desc()
    ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="No tournament found")
    
    return {
        "id": tournament.id,
        "year": tournament.year,
        "tourn_id": tournament.tourn_id,
        "org_id": tournament.org_id,
        "name": tournament.name,
        "start_date": tournament.start_date.isoformat(),
        "end_date": tournament.end_date.isoformat(),
        "status": tournament.status,
        "current_round": tournament.current_round,
    }


@router.get("/tournament/{tournament_id}")
async def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_db)
):
    """Get tournament by ID."""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    return {
        "id": tournament.id,
        "year": tournament.year,
        "tourn_id": tournament.tourn_id,
        "org_id": tournament.org_id,
        "name": tournament.name,
        "start_date": tournament.start_date.isoformat(),
        "end_date": tournament.end_date.isoformat(),
        "status": tournament.status,
        "current_round": tournament.current_round,
    }


@router.post("/tournament/sync")
async def sync_tournament(
    org_id: Optional[str] = None,
    tourn_id: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Sync tournament data from API."""
    sync_service = DataSyncService(db)
    
    try:
        results = sync_service.sync_tournament_data(org_id, tourn_id, year)
        
        if results["errors"]:
            raise HTTPException(
                status_code=500,
                detail=f"Sync completed with errors: {results['errors']}"
            )
        
        return {
            "message": "Tournament data synced successfully",
            "tournament_id": results["tournament"].id,
            "tournament_name": results["tournament"].name,
            "players_synced": results["players_synced"],
            "snapshot_id": results["snapshot"].id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing tournament: {str(e)}")
