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
        results = import_service.import_entries(rows, tournament_id)
        
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
