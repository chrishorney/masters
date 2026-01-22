"""Public score endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Tournament, Entry, DailyScore
from app.services.score_calculator import ScoreCalculatorService

router = APIRouter()


@router.post("/scores/calculate")
async def calculate_scores(
    tournament_id: int = Query(..., description="Tournament ID"),
    round_id: Optional[int] = Query(None, description="Specific round (default: current round)"),
    db: Session = Depends(get_db)
):
    """Calculate scores for all entries in a tournament."""
    calculator = ScoreCalculatorService(db)
    
    try:
        results = calculator.calculate_scores_for_tournament(tournament_id, round_id)
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("message", "Calculation failed"))
        
        return {
            "message": "Scores calculated successfully",
            "tournament_id": results["tournament_id"],
            "round_id": results["round_id"],
            "entries_processed": results["entries_processed"],
            "entries_updated": results["entries_updated"],
            "errors": results.get("errors", [])
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating scores: {str(e)}")


@router.post("/scores/calculate-all")
async def calculate_all_rounds(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """Calculate scores for all completed rounds."""
    calculator = ScoreCalculatorService(db)
    
    try:
        results = calculator.calculate_all_rounds(tournament_id)
        
        return {
            "message": "Scores calculated for all rounds",
            "tournament_id": results["tournament_id"],
            "rounds_processed": results["rounds_processed"],
            "total_entries_processed": results["total_entries_processed"],
            "errors": results.get("errors", [])
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating scores: {str(e)}")


@router.get("/scores/leaderboard")
async def get_leaderboard(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """Get current leaderboard with total scores."""
    # Get tournament
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Get all entries for tournament
    entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
    
    leaderboard = []
    
    for entry in entries:
        # Get all daily scores for this entry
        daily_scores = db.query(DailyScore).filter(
            DailyScore.entry_id == entry.id
        ).order_by(DailyScore.round_id).all()
        
        total_points = sum(score.total_points for score in daily_scores)
        
        leaderboard.append({
            "entry": {
                "id": entry.id,
                "participant_id": entry.participant_id,
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
                "updated_at": entry.updated_at.isoformat(),
                "participant": {
                    "id": entry.participant.id,
                    "name": entry.participant.name,
                    "email": entry.participant.email,
                    "entry_date": entry.participant.entry_date.isoformat(),
                    "paid": entry.participant.paid,
                }
            },
            "total_points": total_points,
            "daily_scores": [
                {
                    "id": score.id,
                    "entry_id": score.entry_id,
                    "round_id": score.round_id,
                    "date": score.date.isoformat(),
                    "base_points": score.base_points,
                    "bonus_points": score.bonus_points,
                    "total_points": score.total_points,
                    "details": score.details,
                    "calculated_at": score.calculated_at.isoformat(),
                }
                for score in daily_scores
            ]
        })
    
    # Sort by total points descending
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
    # Add rank
    for i, item in enumerate(leaderboard, start=1):
        item["rank"] = i
    
    return {
        "tournament": {
            "id": tournament.id,
            "year": tournament.year,
            "tourn_id": tournament.tourn_id,
            "name": tournament.name,
            "start_date": tournament.start_date.isoformat(),
            "end_date": tournament.end_date.isoformat(),
            "status": tournament.status,
            "current_round": tournament.current_round,
        },
        "entries": leaderboard,
        "last_updated": datetime.now().isoformat()
    }
