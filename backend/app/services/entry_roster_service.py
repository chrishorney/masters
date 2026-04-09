"""Admin edits to pool entry rosters (remove golfer, clear points, recalc)."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models import BonusPoint, Entry, Participant, Player, Tournament
from app.services.score_calculator import ScoreCalculatorService

logger = logging.getLogger(__name__)


def _remove_player_from_rebuy_pairs(entry: Entry, player_id: str) -> None:
    """Drop rebuy pairs where either original or rebuy matches player_id."""
    pid = str(player_id)
    rbu = list(entry.rebuy_player_ids or [])
    rbo = list(entry.rebuy_original_player_ids or [])
    if len(rbu) != len(rbo):
        logger.warning(
            "Entry %s rebuy lists length mismatch (orig=%s rebuy=%s); trimming to min length",
            entry.id,
            len(rbo),
            len(rbu),
        )
    pairs: List[Tuple[str, str]] = []
    for o, r in zip(rbo, rbu):
        pairs.append((str(o), str(r)))
    kept_o: List[str] = []
    kept_r: List[str] = []
    for o, r in pairs:
        if o != pid and r != pid:
            kept_o.append(o)
            kept_r.append(r)
    entry.rebuy_original_player_ids = kept_o
    entry.rebuy_player_ids = kept_r
    flag_modified(entry, "rebuy_original_player_ids")
    flag_modified(entry, "rebuy_player_ids")


def _clear_player_from_main_slots(entry: Entry, player_id: str) -> int:
    """Set any main slot matching player_id to None. Returns number of slots cleared."""
    pid = str(player_id)
    cleared = 0
    for i in range(1, 7):
        attr = f"player{i}_id"
        if getattr(entry, attr) == pid:
            setattr(entry, attr, None)
            cleared += 1
    return cleared


def remove_player_from_entry(
    db: Session,
    tournament_id: int,
    entry_id: int,
    player_id: str,
) -> Dict[str, Any]:
    """
    Remove a golfer from an entry's roster for this tournament, delete all bonus rows
    tied to that player for this entry, then recalculate scores for this entry for
    all completed rounds.
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise ValueError("Tournament not found")

    entry = (
        db.query(Entry)
        .filter(Entry.id == entry_id, Entry.tournament_id == tournament_id)
        .first()
    )
    if not entry:
        raise ValueError("Entry not found")

    pid = str(player_id)
    main_before = [
        entry.player1_id,
        entry.player2_id,
        entry.player3_id,
        entry.player4_id,
        entry.player5_id,
        entry.player6_id,
    ]
    in_main = pid in [str(x) for x in main_before if x]
    in_rebuy = pid in [str(x) for x in (entry.rebuy_player_ids or [])] or pid in [
        str(x) for x in (entry.rebuy_original_player_ids or [])
    ]
    if not in_main and not in_rebuy:
        raise ValueError("Player is not on this entry")

    _remove_player_from_rebuy_pairs(entry, pid)
    cleared = _clear_player_from_main_slots(entry, pid)

    deleted_bonuses = (
        db.query(BonusPoint)
        .filter(BonusPoint.entry_id == entry_id, BonusPoint.player_id == pid)
        .delete(synchronize_session=False)
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    calc = ScoreCalculatorService(db)
    current_round = tournament.current_round or 1
    all_errors: List[str] = []
    for rid in range(1, current_round + 1):
        res = calc.calculate_scores_for_tournament(
            tournament_id, round_id=rid, entry_id=entry_id
        )
        for err in res.get("errors") or []:
            all_errors.append(err)

    return {
        "success": len(all_errors) == 0,
        "entry_id": entry_id,
        "player_id": pid,
        "main_slots_cleared": cleared,
        "bonus_rows_deleted": deleted_bonuses,
        "rounds_recalculated": current_round,
        "errors": all_errors,
    }


def list_entries_for_tournament(db: Session, tournament_id: int) -> List[Dict[str, Any]]:
    rows = (
        db.query(Entry, Participant)
        .join(Participant, Entry.participant_id == Participant.id)
        .filter(Entry.tournament_id == tournament_id)
        .order_by(Participant.name.asc())
        .all()
    )
    out: List[Dict[str, Any]] = []
    for entry, participant in rows:
        out.append(
            {
                "id": entry.id,
                "participant_id": participant.id,
                "participant_name": participant.name,
                "participant_email": participant.email,
                "tournament_id": entry.tournament_id,
                "player1_id": entry.player1_id,
                "player2_id": entry.player2_id,
                "player3_id": entry.player3_id,
                "player4_id": entry.player4_id,
                "player5_id": entry.player5_id,
                "player6_id": entry.player6_id,
                "rebuy_player_ids": entry.rebuy_player_ids or [],
                "rebuy_original_player_ids": entry.rebuy_original_player_ids or [],
            }
        )
    return out


def create_participant(
    db: Session,
    name: str,
    email: Optional[str] = None,
    paid: bool = False,
) -> Participant:
    name = (name or "").strip()
    if not name:
        raise ValueError("Participant name is required")
    p = Participant(name=name, email=(email.strip() if email else None), paid=paid)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def create_entry_with_players(
    db: Session,
    tournament_id: int,
    participant_id: int,
    player_ids: List[Optional[str]],
) -> Entry:
    if len(player_ids) != 6:
        raise ValueError("Exactly six player slots are required (use null for empty slots)")
    norm: List[Optional[str]] = []
    for p in player_ids:
        if p is None or (isinstance(p, str) and not p.strip()):
            norm.append(None)
        else:
            norm.append(str(p).strip())
    player_ids = norm

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise ValueError("Tournament not found")
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise ValueError("Participant not found")

    dup = (
        db.query(Entry)
        .filter(
            Entry.participant_id == participant_id,
            Entry.tournament_id == tournament_id,
        )
        .first()
    )
    if dup:
        raise ValueError("This participant already has an entry for this tournament")

    filled = [p for p in player_ids if p]
    if len(filled) < 1:
        raise ValueError("At least one golfer is required")

    for p in filled:
        if not db.query(Player).filter(Player.player_id == p).first():
            raise ValueError(f"Unknown player_id in roster: {p}")

    entry = Entry(
        participant_id=participant_id,
        tournament_id=tournament_id,
        player1_id=player_ids[0],
        player2_id=player_ids[1],
        player3_id=player_ids[2],
        player4_id=player_ids[3],
        player5_id=player_ids[4],
        player6_id=player_ids[5],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_entry_player_slot(
    db: Session,
    tournament_id: int,
    entry_id: int,
    slot: int,
    player_id: Optional[str],
) -> Entry:
    if slot < 1 or slot > 6:
        raise ValueError("slot must be 1–6")
    entry = (
        db.query(Entry)
        .filter(Entry.id == entry_id, Entry.tournament_id == tournament_id)
        .first()
    )
    if not entry:
        raise ValueError("Entry not found")
    if player_id is not None and str(player_id).strip():
        pid = str(player_id).strip()
        if not db.query(Player).filter(Player.player_id == pid).first():
            raise ValueError(f"Unknown player_id: {pid}")
        setattr(entry, f"player{slot}_id", pid)
    else:
        setattr(entry, f"player{slot}_id", None)
    db.commit()
    db.refresh(entry)

    calc = ScoreCalculatorService(db)
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    current_round = (tournament.current_round or 1) if tournament else 1
    for rid in range(1, current_round + 1):
        calc.calculate_scores_for_tournament(
            tournament_id, round_id=rid, entry_id=entry_id
        )
    return entry
