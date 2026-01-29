"""Public tournament endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Tournament
from app.services.data_sync import DataSyncService

router = APIRouter()


@router.get("/discord/invite")
async def get_discord_invite():
    """Get Discord server invite URL (public endpoint)."""
    from app.config import settings
    
    if not settings.discord_invite_url:
        raise HTTPException(
            status_code=404,
            detail="Discord invite URL not configured"
        )
    
    return {
        "invite_url": settings.discord_invite_url
    }


@router.get("/discord/widget")
async def get_discord_widget():
    """Get Discord server widget info (public endpoint)."""
    from app.config import settings
    
    if not settings.discord_server_id:
        raise HTTPException(
            status_code=404,
            detail="Discord server ID not configured"
        )
    
    return {
        "server_id": settings.discord_server_id,
        "widget_url": f"https://discord.com/widget?id={settings.discord_server_id}&theme=dark"
    }


@router.get("/tournament/list")
async def list_tournaments(
    db: Session = Depends(get_db)
):
    """List all tournaments in the database."""
    tournaments = db.query(Tournament).order_by(
        Tournament.year.desc(),
        Tournament.start_date.desc()
    ).all()
    
    return {
        "tournaments": [
            {
                "id": t.id,
                "year": t.year,
                "tourn_id": t.tourn_id,
                "org_id": t.org_id,
                "name": t.name,
                "start_date": t.start_date.isoformat(),
                "end_date": t.end_date.isoformat(),
                "status": t.status,
                "current_round": t.current_round,
            }
            for t in tournaments
        ],
        "total": len(tournaments)
    }


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
            error_msg = "; ".join(results["errors"])
            # Include error details if available (for debugging)
            if "error_details" in results:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Sync error details: {results['error_details']}")
            raise HTTPException(
                status_code=500,
                detail=f"Sync completed with errors: {error_msg}"
            )
        
        if not results.get("tournament"):
            raise HTTPException(
                status_code=500,
                detail="Sync failed: No tournament was created or updated"
            )
        
        return {
            "message": "Tournament data synced successfully",
            "tournament_id": results["tournament"].id,
            "tournament_name": results["tournament"].name,
            "current_round": results["tournament"].current_round,
            "players_synced": results["players_synced"],
            "snapshot_id": results["snapshot"].id if results.get("snapshot") else None,
            "snapshot_round": results["snapshot"].round_id if results.get("snapshot") else None,
            "scorecards_fetched": results.get("scorecards_fetched", 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in sync endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error syncing tournament: {str(e) or type(e).__name__}"
        )


@router.post("/tournament/sync-round")
async def sync_round(
    tournament_id: int,
    round_id: int,
    db: Session = Depends(get_db)
):
    """
    Sync data for a specific round by fetching scorecards and reconstructing leaderboard.
    
    This is useful for:
    - Syncing historical rounds that weren't captured
    - Recovery if round data was lost
    - Testing with specific round data
    
    Args:
        tournament_id: Tournament ID in database
        round_id: Round number to sync (1-4)
    """
    if round_id < 1 or round_id > 4:
        raise HTTPException(
            status_code=400,
            detail="Round ID must be between 1 and 4"
        )
    
    sync_service = DataSyncService(db)
    
    try:
        # Get tournament to pass org_id, tourn_id, year
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")
        
        results = sync_service.sync_round_data(
            tournament_id=tournament_id,
            round_id=round_id,
            org_id=tournament.org_id,
            tourn_id=tournament.tourn_id,
            year=tournament.year
        )
        
        if results["errors"]:
            error_msg = "; ".join(results["errors"])
            raise HTTPException(
                status_code=500,
                detail=f"Sync completed with errors: {error_msg}"
            )
        
        if not results.get("snapshot"):
            raise HTTPException(
                status_code=500,
                detail="Sync failed: No snapshot was created"
            )
        
        return {
            "message": f"Round {round_id} data synced successfully",
            "tournament_id": results["tournament"].id,
            "tournament_name": results["tournament"].name,
            "round_id": results["round_id"],
            "snapshot_id": results["snapshot"].id,
            "players_processed": results["players_processed"],
            "scorecards_fetched": results["scorecards_fetched"],
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in sync-round endpoint: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error syncing round: {str(e) or type(e).__name__}"
        )
