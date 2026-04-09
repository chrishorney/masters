"""Admin CRUD for pool entries and rosters."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import entry_roster_service as roster

router = APIRouter()


class CreateParticipantBody(BaseModel):
    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    paid: bool = False


class CreateEntryBody(BaseModel):
    """Either participant_id (existing) or participant (create new person) is required."""

    participant_id: Optional[int] = None
    participant: Optional[CreateParticipantBody] = None
    player1_id: Optional[str] = None
    player2_id: Optional[str] = None
    player3_id: Optional[str] = None
    player4_id: Optional[str] = None
    player5_id: Optional[str] = None
    player6_id: Optional[str] = None


class UpdateSlotBody(BaseModel):
    player_id: Optional[str] = None


@router.get("/tournaments/{tournament_id}/entries")
def list_entries(tournament_id: int, db: Session = Depends(get_db)):
    """List all entries for a tournament (participant + player slots)."""
    return {"entries": roster.list_entries_for_tournament(db, tournament_id)}


@router.post("/participants")
def create_participant(body: CreateParticipantBody, db: Session = Depends(get_db)):
    """Create a pool participant (person) without an entry."""
    try:
        p = roster.create_participant(
            db, name=body.name, email=body.email, paid=body.paid
        )
        return {
            "id": p.id,
            "name": p.name,
            "email": p.email,
            "paid": p.paid,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/participants")
def search_participants(
    q: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List participants (optional name filter) for linking to new entries."""
    from app.models import Participant

    query = db.query(Participant).order_by(Participant.name.asc())
    if q and q.strip():
        term = f"%{q.strip()}%"
        from sqlalchemy import or_

        query = query.filter(
            or_(
                Participant.name.ilike(term),
                Participant.email.ilike(term),
            )
        )
    rows = query.limit(min(limit, 200)).all()
    return {
        "participants": [
            {"id": p.id, "name": p.name, "email": p.email, "paid": p.paid}
            for p in rows
        ]
    }


@router.post("/tournaments/{tournament_id}/entries")
def create_entry(tournament_id: int, body: CreateEntryBody, db: Session = Depends(get_db)):
    """
    Create an entry for the tournament: six slots (null = empty).
    At least one golfer must be set.
    Use participant_id for an existing person, or participant: {name, ...} to create one.
    """
    try:
        player_ids: List[Optional[str]] = [
            body.player1_id,
            body.player2_id,
            body.player3_id,
            body.player4_id,
            body.player5_id,
            body.player6_id,
        ]
        pid = body.participant_id
        if pid is None and body.participant:
            p = roster.create_participant(
                db,
                name=body.participant.name,
                email=body.participant.email,
                paid=body.participant.paid,
            )
            pid = p.id
        if not pid:
            raise ValueError("participant_id or participant is required")

        entry = roster.create_entry_with_players(db, tournament_id, pid, player_ids)
        return {
            "id": entry.id,
            "participant_id": entry.participant_id,
            "tournament_id": entry.tournament_id,
            "player1_id": entry.player1_id,
            "player2_id": entry.player2_id,
            "player3_id": entry.player3_id,
            "player4_id": entry.player4_id,
            "player5_id": entry.player5_id,
            "player6_id": entry.player6_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/tournaments/{tournament_id}/entries/{entry_id}/slots/{slot}")
def update_entry_slot(
    tournament_id: int,
    entry_id: int,
    slot: int,
    body: UpdateSlotBody,
    db: Session = Depends(get_db),
):
    """Set one roster slot (1–6) to a golfer ID or null to clear."""
    try:
        e = roster.update_entry_player_slot(
            db, tournament_id, entry_id, slot, body.player_id
        )
        return {
            "id": e.id,
            "player1_id": e.player1_id,
            "player2_id": e.player2_id,
            "player3_id": e.player3_id,
            "player4_id": e.player4_id,
            "player5_id": e.player5_id,
            "player6_id": e.player6_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/tournaments/{tournament_id}/entries/{entry_id}/players/{player_id}")
def remove_player_from_entry_route(
    tournament_id: int,
    entry_id: int,
    player_id: str,
    db: Session = Depends(get_db),
):
    """
    Remove a golfer from this entry (main roster or rebuy), delete all bonus/points
    rows for that player on this entry, and recalculate scores for this entry.
    """
    try:
        return roster.remove_player_from_entry(db, tournament_id, entry_id, player_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
