"""Admin endpoints for tournament-level settings."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tournament


router = APIRouter()


class LeaderboardVisibilityUpdate(BaseModel):
  """Payload for updating tournament leaderboard visibility."""
  tournament_id: int
  show: bool


@router.get("/tournament/leaderboard-visibility")
async def get_leaderboard_visibility(
  tournament_id: int = Query(..., description="Tournament ID"),
  db: Session = Depends(get_db),
):
  """Get whether the Tournament Leaderboard tab should be shown for this tournament."""
  tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
  if not tournament:
    raise HTTPException(status_code=404, detail="Tournament not found")

  hide_leaderboard = False
  if tournament.api_data and isinstance(tournament.api_data, dict):
    hide_leaderboard = bool(tournament.api_data.get("hideTournamentLeaderboard", False))

  return {
    "tournament_id": tournament.id,
    "show_tournament_leaderboard": not hide_leaderboard,
  }


@router.post("/tournament/leaderboard-visibility")
async def update_leaderboard_visibility(
  payload: LeaderboardVisibilityUpdate = Body(...),
  db: Session = Depends(get_db),
):
  """Update whether the Tournament Leaderboard tab should be shown for this tournament."""
  tournament = db.query(Tournament).filter(Tournament.id == payload.tournament_id).first()
  if not tournament:
    raise HTTPException(status_code=404, detail="Tournament not found")

  # Ensure api_data is a dict we can safely modify
  if tournament.api_data is None or not isinstance(tournament.api_data, dict):
    tournament.api_data = {}

  tournament.api_data["hideTournamentLeaderboard"] = not payload.show
  db.add(tournament)
  db.commit()
  db.refresh(tournament)

  return {
    "tournament_id": tournament.id,
    "show_tournament_leaderboard": payload.show,
  }

