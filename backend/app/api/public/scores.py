"""Public score endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

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
    # Get all entries for tournament
    entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
    
    leaderboard = []
    
    for entry in entries:
        # Get all daily scores for this entry
        daily_scores = db.query(DailyScore).filter(
            DailyScore.entry_id == entry.id
        ).all()
        
        total_points = sum(score.total_points for score in daily_scores)
        
        leaderboard.append({
            "entry_id": entry.id,
            "participant_name": entry.participant.name,
            "total_points": total_points,
            "round_scores": [
                {
                    "round_id": score.round_id,
                    "base_points": score.base_points,
                    "bonus_points": score.bonus_points,
                    "total_points": score.total_points
                }
                for score in daily_scores
            ]
        })
    
    # Sort by total points descending
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
    return {
        "tournament_id": tournament_id,
        "leaderboard": leaderboard
    }
