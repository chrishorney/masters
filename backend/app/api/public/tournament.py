"""Public tournament endpoints."""
import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Tournament
from app.services.data_sync import DataSyncService

router = APIRouter()
logger = logging.getLogger(__name__)

# Cache Discord widget invite for 10 minutes so we don't hit Discord every request
_discord_invite_cache: Optional[dict] = None
DISCORD_INVITE_CACHE_TTL_SEC = 600


async def _fetch_discord_invite_from_widget(server_id: str) -> Optional[str]:
    """Fetch current invite URL from Discord's widget API (same source as the widget iframe)."""
    try:
        import httpx
        url = f"https://discord.com/api/guilds/{server_id}/widget.json"
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return None
            data = r.json()
            return (data.get("instant_invite") or "").strip() or None
    except Exception as e:
        logger.debug("Could not fetch Discord widget invite: %s", e)
        return None


@router.get("/discord/invite")
async def get_discord_invite():
    """
    Get Discord server invite URL (public endpoint).
    Prefers the invite from Discord's widget API (same as the widget's Join button);
    falls back to DISCORD_INVITE_URL if widget invite is not available.
    """
    from app.config import settings

    now = time.time()
    global _discord_invite_cache
    if _discord_invite_cache and _discord_invite_cache.get("expires_at", 0) > now:
        return {"invite_url": _discord_invite_cache["invite_url"]}

    invite_url: Optional[str] = None

    # Prefer widget API so the top "Join Discord" button uses the same invite as the widget
    if settings.discord_server_id:
        invite_url = await _fetch_discord_invite_from_widget(settings.discord_server_id)
        if invite_url:
            _discord_invite_cache = {"invite_url": invite_url, "expires_at": now + DISCORD_INVITE_CACHE_TTL_SEC}

    if not invite_url and settings.discord_invite_url:
        invite_url = settings.discord_invite_url
        _discord_invite_cache = {"invite_url": invite_url, "expires_at": now + DISCORD_INVITE_CACHE_TTL_SEC}

    if not invite_url:
        raise HTTPException(
            status_code=404,
            detail="Discord invite URL not configured. Set DISCORD_SERVER_ID (widget) and enable widget with instant invite in Discord, or set DISCORD_INVITE_URL."
        )

    return {"invite_url": invite_url}


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
    
    hide_leaderboard = False
    if tournament.api_data and isinstance(tournament.api_data, dict):
        hide_leaderboard = bool(tournament.api_data.get("hideTournamentLeaderboard", False))

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
        "show_tournament_leaderboard": not hide_leaderboard,
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
    
    hide_leaderboard = False
    if tournament.api_data and isinstance(tournament.api_data, dict):
        hide_leaderboard = bool(tournament.api_data.get("hideTournamentLeaderboard", False))

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
        "show_tournament_leaderboard": not hide_leaderboard,
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
