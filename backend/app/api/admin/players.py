"""Admin endpoints for player lookup."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Player, Tournament

router = APIRouter()


@router.get("/players/search")
async def search_players(
    name: str = Query(..., description="Player name to search"),
    tournament_id: Optional[int] = Query(None, description="Limit to tournament players"),
    db: Session = Depends(get_db)
):
    """Search for players by name."""
    query = db.query(Player)
    
    # Search by name
    search_term = f"%{name}%"
    query = query.filter(
        (Player.full_name.ilike(search_term)) |
        (Player.first_name.ilike(search_term)) |
        (Player.last_name.ilike(search_term))
    )
    
    # If tournament specified, get players from that tournament's leaderboard
    if tournament_id:
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if tournament:
            from app.models import ScoreSnapshot
            snapshot = db.query(ScoreSnapshot).filter(
                ScoreSnapshot.tournament_id == tournament_id
            ).order_by(ScoreSnapshot.timestamp.desc()).first()
            
            if snapshot:
                leaderboard_player_ids = [
                    str(row.get("playerId", ""))
                    for row in snapshot.leaderboard_data.get("leaderboardRows", [])
                ]
                query = query.filter(Player.player_id.in_(leaderboard_player_ids))
    
    players = query.limit(20).all()
    
    return {
        "players": [
            {
                "player_id": p.player_id,
                "full_name": p.full_name,
                "first_name": p.first_name,
                "last_name": p.last_name
            }
            for p in players
        ]
    }


@router.get("/players/tournament/{tournament_id}")
async def get_tournament_players(
    tournament_id: int,
    db: Session = Depends(get_db)
):
    """Get all players in a tournament's leaderboard."""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    if not tournament:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    from app.models import ScoreSnapshot
    snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    if not snapshot:
        return {"players": []}
    
    leaderboard_rows = snapshot.leaderboard_data.get("leaderboardRows", [])
    
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
