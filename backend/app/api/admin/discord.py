"""Admin endpoints for Discord testing and management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Tournament
from app.services.discord import get_discord_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/discord/test")
async def test_discord_notification(
    notification_type: str = Query(..., description="Type: hole_in_one, eagle, double_eagle, new_leader, big_move, round_complete, tournament_start"),
    tournament_id: Optional[int] = Query(None, description="Tournament ID (required for some notification types)"),
    db: Session = Depends(get_db)
):
    """
    Test Discord notification by sending a sample message.
    
    This endpoint allows you to test if Discord integration is working correctly.
    """
    discord_service = get_discord_service()
    
    if not discord_service.enabled:
        raise HTTPException(
            status_code=400,
            detail="Discord is not enabled. Set DISCORD_ENABLED=true and DISCORD_WEBHOOK_URL in environment variables."
        )
    
    tournament = None
    if tournament_id:
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")
    
    try:
        if notification_type == "hole_in_one":
            success = await discord_service.notify_hole_in_one(
                player_name="Test Player",
                hole=7,
                round_id=1,
                tournament_name=tournament.name if tournament else "Test Tournament"
            )
        elif notification_type == "eagle":
            success = await discord_service.notify_eagle(
                player_name="Test Player",
                hole=12,
                round_id=1,
                tournament_name=tournament.name if tournament else "Test Tournament"
            )
        elif notification_type == "double_eagle":
            success = await discord_service.notify_double_eagle(
                player_name="Test Player",
                hole=15,
                round_id=1,
                tournament_name=tournament.name if tournament else "Test Tournament"
            )
        elif notification_type == "new_leader":
            success = await discord_service.notify_new_leader(
                entry_name="Test Entry",
                total_points=45.0,
                previous_leader_name="Previous Leader",
                round_id=1,
                tournament_name=tournament.name if tournament else "Test Tournament"
            )
        elif notification_type == "big_move":
            success = await discord_service.notify_big_position_change(
                entry_name="Test Entry",
                old_position=15,
                new_position=3,
                total_points=38.5,
                round_id=1
            )
        elif notification_type == "round_complete":
            success = await discord_service.notify_round_complete(
                round_id=1,
                leader_name="Test Leader",
                leader_points=45.0,
                total_entries=25,
                tournament_name=tournament.name if tournament else "Test Tournament"
            )
        elif notification_type == "tournament_start":
            success = await discord_service.notify_tournament_start(
                tournament_name=tournament.name if tournament else "Test Tournament",
                year=tournament.year if tournament else 2026,
                entry_count=25
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown notification type: {notification_type}. Valid types: hole_in_one, eagle, double_eagle, new_leader, big_move, round_complete, tournament_start"
            )
        
        if success:
            return {
                "success": True,
                "message": f"Test {notification_type} notification sent successfully! Check your Discord channel.",
                "notification_type": notification_type
            }
        else:
            return {
                "success": False,
                "message": f"Failed to send {notification_type} notification. Check logs for details.",
                "notification_type": notification_type
            }
    except Exception as e:
        logger.error(f"Error sending test Discord notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error sending test notification: {str(e)}"
        )


@router.get("/discord/status")
async def get_discord_status():
    """Get Discord integration status."""
    from app.config import settings
    discord_service = get_discord_service()
    
    return {
        "enabled": discord_service.enabled,
        "webhook_configured": bool(discord_service.webhook_url),
        "invite_url": settings.discord_invite_url,
        "status": "enabled" if discord_service.enabled else "disabled"
    }
