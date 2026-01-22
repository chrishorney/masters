"""Admin endpoints for managing bonus points."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import BonusPoint, Entry, Tournament
from app.services.scoring import ScoringService

router = APIRouter()


class BonusPointCreate(BaseModel):
    """Schema for creating a bonus point."""
    tournament_id: int
    round_id: int
    player_id: str
    bonus_type: str  # "gir_leader" or "fairways_leader"
    points: float = 1.0


class BonusPointBulkCreate(BaseModel):
    """Schema for bulk creating bonus points."""
    tournament_id: int
    round_id: int
    bonuses: List[dict]  # [{"player_id": "123", "bonus_type": "gir_leader"}, ...]


@router.post("/bonus-points/add")
async def add_bonus_point(
    bonus: BonusPointCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Add a manual bonus point (GIR leader, Fairways leader, etc.).
    
    This will automatically award the bonus to all entries that have this player.
    """
    # Verify tournament exists
    tournament = db.query(Tournament).filter(
        Tournament.id == bonus.tournament_id
    ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Validate bonus type
    valid_types = ["gir_leader", "fairways_leader"]
    if bonus.bonus_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid bonus type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Find all entries that have this player
    entries = db.query(Entry).filter(
        Entry.tournament_id == bonus.tournament_id
    ).all()
    
    matching_entries = []
    for entry in entries:
        player_ids = [
            entry.player1_id, entry.player2_id, entry.player3_id,
            entry.player4_id, entry.player5_id, entry.player6_id
        ]
        
        # Check if player is in original lineup
        if bonus.player_id in player_ids:
            matching_entries.append(entry)
        # Check if player is in rebuy lineup (for rounds 3-4)
        elif bonus.round_id >= 3 and entry.rebuy_player_ids:
            if bonus.player_id in entry.rebuy_player_ids:
                matching_entries.append(entry)
    
    if not matching_entries:
        return {
            "message": f"No entries found with player {bonus.player_id}",
            "bonus_type": bonus.bonus_type,
            "round_id": bonus.round_id,
            "entries_updated": 0
        }
    
    # Create bonus points for all matching entries
    created_count = 0
    for entry in matching_entries:
        # Check if bonus already exists
        existing = db.query(BonusPoint).filter(
            BonusPoint.entry_id == entry.id,
            BonusPoint.round_id == bonus.round_id,
            BonusPoint.bonus_type == bonus.bonus_type,
            BonusPoint.player_id == bonus.player_id
        ).first()
        
        if not existing:
            bonus_point = BonusPoint(
                entry_id=entry.id,
                round_id=bonus.round_id,
                bonus_type=bonus.bonus_type,
                points=bonus.points,
                player_id=bonus.player_id
            )
            db.add(bonus_point)
            created_count += 1
    
    db.commit()
    
    # Recalculate daily scores for affected entries
    scoring_service = ScoringService(db)
    updated_count = 0
    
    for entry in matching_entries:
        # Get the score snapshot for this round
        from app.models import ScoreSnapshot
        snapshot = db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == bonus.tournament_id,
            ScoreSnapshot.round_id == bonus.round_id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        if snapshot:
            try:
                scoring_service.calculate_and_save_daily_score(
                    entry=entry,
                    tournament=tournament,
                    leaderboard_data=snapshot.leaderboard_data,
                    scorecard_data=snapshot.scorecard_data or {},
                    round_id=bonus.round_id,
                    score_date=tournament.start_date  # Approximate date
                )
                updated_count += 1
            except Exception as e:
                # Log error but continue
                pass
    
    return {
        "message": "Bonus points added successfully",
        "bonus_type": bonus.bonus_type,
        "round_id": bonus.round_id,
        "player_id": bonus.player_id,
        "entries_found": len(matching_entries),
        "bonus_points_created": created_count,
        "scores_updated": updated_count
    }


@router.post("/bonus-points/add-bulk")
async def add_bonus_points_bulk(
    bulk_data: BonusPointBulkCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Add multiple bonus points at once.
    
    Example:
    {
        "tournament_id": 1,
        "round_id": 1,
        "bonuses": [
            {"player_id": "50525", "bonus_type": "gir_leader"},
            {"player_id": "47504", "bonus_type": "fairways_leader"}
        ]
    }
    """
    tournament = db.query(Tournament).filter(
        Tournament.id == bulk_data.tournament_id
    ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    results = []
    
    for bonus_data in bulk_data.bonuses:
        player_id = bonus_data.get("player_id")
        bonus_type = bonus_data.get("bonus_type")
        points = bonus_data.get("points", 1.0)
        
        if not player_id or not bonus_type:
            continue
        
        # Use the same logic as single add
        bonus_create = BonusPointCreate(
            tournament_id=bulk_data.tournament_id,
            round_id=bulk_data.round_id,
            player_id=player_id,
            bonus_type=bonus_type,
            points=points
        )
        
        try:
            result = await add_bonus_point(bonus_create, db)
            results.append({
                "player_id": player_id,
                "bonus_type": bonus_type,
                "success": True,
                "entries_updated": result.get("entries_updated", 0)
            })
        except Exception as e:
            results.append({
                "player_id": player_id,
                "bonus_type": bonus_type,
                "success": False,
                "error": str(e)
            })
    
    return {
        "message": f"Processed {len(bulk_data.bonuses)} bonus points",
        "results": results
    }


@router.get("/bonus-points/list")
async def list_bonus_points(
    tournament_id: int = Query(..., description="Tournament ID"),
    round_id: Optional[int] = Query(None, description="Round ID (optional)"),
    db: Session = Depends(get_db)
):
    """List all bonus points for a tournament."""
    query = db.query(BonusPoint).join(Entry).filter(
        Entry.tournament_id == tournament_id
    )
    
    if round_id:
        query = query.filter(BonusPoint.round_id == round_id)
    
    bonus_points = query.all()
    
    return {
        "tournament_id": tournament_id,
        "round_id": round_id,
        "bonus_points": [
            {
                "id": bp.id,
                "entry_id": bp.entry_id,
                "round_id": bp.round_id,
                "bonus_type": bp.bonus_type,
                "points": bp.points,
                "player_id": bp.player_id,
                "awarded_at": bp.awarded_at.isoformat()
            }
            for bp in bonus_points
        ]
    }


@router.delete("/bonus-points/{bonus_point_id}")
async def delete_bonus_point(
    bonus_point_id: int,
    db: Session = Depends(get_db)
):
    """Delete a bonus point and recalculate affected entry scores."""
    bonus_point = db.query(BonusPoint).filter(
        BonusPoint.id == bonus_point_id
    ).first()
    
    if not bonus_point:
        raise HTTPException(status_code=404, detail="Bonus point not found")
    
    entry_id = bonus_point.entry_id
    round_id = bonus_point.round_id
    
    # Delete the bonus point
    db.delete(bonus_point)
    db.commit()
    
    # Recalculate the entry's score for this round
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if entry:
        tournament = db.query(Tournament).filter(
            Tournament.id == entry.tournament_id
        ).first()
        
        if tournament:
            from app.models import ScoreSnapshot
            snapshot = db.query(ScoreSnapshot).filter(
                ScoreSnapshot.tournament_id == tournament.id,
                ScoreSnapshot.round_id == round_id
            ).order_by(ScoreSnapshot.timestamp.desc()).first()
            
            if snapshot:
                scoring_service = ScoringService(db)
                scoring_service.calculate_and_save_daily_score(
                    entry=entry,
                    tournament=tournament,
                    leaderboard_data=snapshot.leaderboard_data,
                    scorecard_data=snapshot.scorecard_data or {},
                    round_id=round_id,
                    score_date=tournament.start_date
                )
    
    return {"message": "Bonus point deleted and scores recalculated"}
