"""Public endpoints for entry details."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Entry, DailyScore, BonusPoint, Tournament, Player

router = APIRouter()


@router.get("/entry/{entry_id}")
async def get_entry_details(
    entry_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific entry."""
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Get tournament
    tournament = db.query(Tournament).filter(Tournament.id == entry.tournament_id).first()
    
    # Get all daily scores
    daily_scores = db.query(DailyScore).filter(
        DailyScore.entry_id == entry.id
    ).order_by(DailyScore.round_id).all()
    
    # Get all bonus points
    bonus_points = db.query(BonusPoint).filter(
        BonusPoint.entry_id == entry.id
    ).order_by(BonusPoint.round_id, BonusPoint.bonus_type).all()
    
    # Get player information
    player_ids = [
        entry.player1_id, entry.player2_id, entry.player3_id,
        entry.player4_id, entry.player5_id, entry.player6_id
    ]
    
    players = {}
    for player_id in player_ids:
        player = db.query(Player).filter(Player.player_id == player_id).first()
        if player:
            players[player_id] = {
                "player_id": player.player_id,
                "first_name": player.first_name,
                "last_name": player.last_name,
                "full_name": player.full_name,
            }
    
    # Get rebuy player info if applicable
    rebuy_players = {}
    if entry.rebuy_player_ids:
        for rebuy_id in entry.rebuy_player_ids:
            player = db.query(Player).filter(Player.player_id == rebuy_id).first()
            if player:
                rebuy_players[rebuy_id] = {
                    "player_id": player.player_id,
                    "first_name": player.first_name,
                    "last_name": player.last_name,
                    "full_name": player.full_name,
                }
    
    # Calculate totals
    total_points = sum(score.total_points for score in daily_scores)
    total_base_points = sum(score.base_points for score in daily_scores)
    total_bonus_points = sum(score.bonus_points for score in daily_scores)
    
    return {
        "entry": {
            "id": entry.id,
            "participant": {
                "id": entry.participant.id,
                "name": entry.participant.name,
                "email": entry.participant.email,
            },
            "tournament_id": entry.tournament_id,
            "player1_id": entry.player1_id,
            "player2_id": entry.player2_id,
            "player3_id": entry.player3_id,
            "player4_id": entry.player4_id,
            "player5_id": entry.player5_id,
            "player6_id": entry.player6_id,
            "rebuy_player_ids": entry.rebuy_player_ids or [],
            "rebuy_type": entry.rebuy_type,
            "rebuy_original_player_ids": entry.rebuy_original_player_ids or [],
            "weekend_bonus_earned": entry.weekend_bonus_earned,
            "weekend_bonus_forfeited": entry.weekend_bonus_forfeited,
            "created_at": entry.created_at.isoformat(),
        },
        "tournament": {
            "id": tournament.id if tournament else None,
            "name": tournament.name if tournament else None,
            "year": tournament.year if tournament else None,
            "current_round": tournament.current_round if tournament else None,
        },
        "players": players,
        "rebuy_players": rebuy_players,
        "daily_scores": [
            {
                "id": score.id,
                "round_id": score.round_id,
                "date": score.date.isoformat(),
                "base_points": score.base_points,
                "bonus_points": score.bonus_points,
                "total_points": score.total_points,
                "details": score.details,
                "calculated_at": score.calculated_at.isoformat(),
            }
            for score in daily_scores
        ],
        "bonus_points": [
            {
                "id": bp.id,
                "round_id": bp.round_id,
                "bonus_type": bp.bonus_type,
                "points": bp.points,
                "player_id": bp.player_id,
                "awarded_at": bp.awarded_at.isoformat(),
            }
            for bp in bonus_points
        ],
        "totals": {
            "total_points": total_points,
            "total_base_points": total_base_points,
            "total_bonus_points": total_bonus_points,
        }
    }
