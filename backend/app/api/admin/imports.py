"""Admin endpoints for SmartSheet imports."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.import_service import ImportService

router = APIRouter()


@router.post("/import/entries")
async def import_entries(
    tournament_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import entries from SmartSheet CSV export.
    
    Expected CSV format:
    - Participant Name
    - Player 1 Name
    - Player 2 Name
    - Player 3 Name
    - Player 4 Name
    - Player 5 Name
    - Player 6 Name
    """
    if not file.filename.endswith(('.csv', '.CSV')):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )
    
    try:
        file_content = await file.read()
        import_service = ImportService(db)
        rows = import_service.parse_csv(file_content)
        
        # Check if this is the first entry import for this tournament
        from app.models import Entry, Tournament
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        existing_entries_count = db.query(Entry).filter(Entry.tournament_id == tournament_id).count()
        is_first_import = existing_entries_count == 0
        
        results = import_service.import_entries(rows, tournament_id)
        
        # Notify Discord if this is the first import (tournament start)
        if is_first_import and results.get("imported", 0) > 0 and tournament:
            import asyncio
            from app.services.discord import get_discord_service
            
            async def notify_tournament_start():
                try:
                    discord_service = get_discord_service()
                    if discord_service and discord_service.enabled:
                        total_entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).count()
                        await discord_service.notify_tournament_start(
                            tournament_name=tournament.name,
                            year=tournament.year,
                            entry_count=total_entries
                        )
                        
                        # Also send push notification
                        try:
                            from app.services.push_notifications import get_push_service
                            from app.models import PushSubscription
                            
                            push_service = get_push_service()
                            if push_service.enabled:
                                subscriptions = db.query(PushSubscription).filter(
                                    PushSubscription.active == True
                                ).all()
                                
                                if subscriptions:
                                    title = "🏌️ Tournament Started!"
                                    body = f"{tournament.name} ({tournament.year}) has begun with {total_entries} entries!"
                                    
                                    for sub in subscriptions:
                                        push_service.send_notification(
                                            subscription=sub.subscription_data,
                                            title=title,
                                            body=body,
                                            url="/"
                                        )
                        except Exception as push_error:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Push notification for tournament start failed (non-critical): {push_error}")
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Discord tournament start notification failed (non-critical): {e}")
            
            # Fire-and-forget
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(notify_tournament_start())
                else:
                    loop.run_until_complete(notify_tournament_start())
            except Exception:
                pass  # Ignore if we can't schedule
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.post("/import/rebuys")
async def import_rebuys(
    tournament_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import rebuys from SmartSheet CSV export.
    
    Expected CSV format:
    - Participant Name
    - Original Player Name
    - Rebuy Player Name
    - Rebuy Type (missed_cut or underperformer)
    """
    if not file.filename.endswith(('.csv', '.CSV')):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )
    
    try:
        file_content = await file.read()
        import_service = ImportService(db)
        rows = import_service.parse_csv(file_content)
        results = import_service.import_rebuys(rows, tournament_id)
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/import/preview")
async def preview_import(
    tournament_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Preview player matching for a tournament.
    Useful for testing player name matching before import.
    """
    from app.models import Tournament, ScoreSnapshot
    
    tournament = db.query(Tournament).filter(
        Tournament.id == tournament_id
    ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Get latest snapshot
    snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    if not snapshot:
        return {
            "message": "No leaderboard data available for this tournament",
            "players": []
        }
    
    leaderboard_rows = snapshot.leaderboard_data.get("leaderboardRows", [])[:limit]
    
    players = []
    for row in leaderboard_rows:
        players.append({
            "player_id": str(row.get("playerId", "")),
            "first_name": row.get("firstName", ""),
            "last_name": row.get("lastName", ""),
            "full_name": f"{row.get('firstName', '')} {row.get('lastName', '')}".strip(),
            "position": row.get("position"),
            "status": row.get("status")
        })
    
    return {
        "tournament_id": tournament_id,
        "tournament_name": tournament.name,
        "players": players
    }
