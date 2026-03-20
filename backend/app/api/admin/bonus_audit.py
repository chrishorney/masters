"""Admin API: bonus audit snapshots (scorecard-based, stored for reconciliation)."""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import BonusAuditRun, BonusAuditLine
from app.services.bonus_audit_service import run_bonus_audit

logger = logging.getLogger(__name__)

router = APIRouter()


def _serialize_line(line: BonusAuditLine) -> Dict[str, Any]:
    return {
        "entry_id": line.entry_id,
        "participant_name": line.participant_name,
        "player_id": line.player_id,
        "player_name": line.player_name,
        "bonus_type": line.bonus_type,
        "points": line.points,
        "hole": line.hole,
    }


def _serialize_run(run: BonusAuditRun, include_lines: bool) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "id": run.id,
        "tournament_id": run.tournament_id,
        "round_id": run.round_id,
        "status": run.status,
        "trigger_source": run.trigger_source,
        "players_checked": run.players_checked,
        "scorecards_fetched": run.scorecards_fetched,
        "entries_audited": run.entries_audited,
        "bonus_lines_count": run.bonus_lines_count,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }
    if include_lines and run.lines is not None:
        ordered = sorted(run.lines, key=lambda x: (x.entry_id, x.id))
        data["lines"] = [_serialize_line(l) for l in ordered]
    return data


@router.post("/bonus-audit/run")
async def post_bonus_audit_run(
    tournament_id: int = Query(..., description="Tournament ID"),
    round_id: int = Query(..., ge=1, le=4, description="Round 1–4"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Run a bonus audit: fetch scorecards for all entry players, merge with the latest
    snapshot for the round, compute bonuses using the same rules as live scoring
    (without mutating weekend_bonus_earned), and store results in bonus_audit_* tables.

    Does not write to `bonus_points` or recalculate daily scores.
    """
    try:
        run, lines, errors = run_bonus_audit(
            db, tournament_id=tournament_id, round_id=round_id, trigger_source="admin"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("bonus audit run failed")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "run": _serialize_run(run, include_lines=False),
        "lines": lines,
        "errors": errors,
        "message": (
            f"Audit run #{run.id} stored: {run.bonus_lines_count} bonus line(s) "
            f"across {run.entries_audited} entries (round {round_id})."
        ),
    }


@router.get("/bonus-audit/runs/{run_id}")
async def get_bonus_audit_run(
    run_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Load a stored audit run and all its lines."""
    run = (
        db.query(BonusAuditRun)
        .options(joinedload(BonusAuditRun.lines))
        .filter(BonusAuditRun.id == run_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    return {"success": True, "run": _serialize_run(run, include_lines=True)}


@router.get("/bonus-audit/runs")
async def list_bonus_audit_runs(
    tournament_id: int = Query(...),
    round_id: Optional[int] = Query(None, ge=1, le=4),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Recent audit runs for a tournament (optionally filtered by round)."""
    q = db.query(BonusAuditRun).filter(BonusAuditRun.tournament_id == tournament_id)
    if round_id is not None:
        q = q.filter(BonusAuditRun.round_id == round_id)
    runs = q.order_by(BonusAuditRun.created_at.desc()).limit(limit).all()
    return {
        "runs": [
            {
                "id": r.id,
                "round_id": r.round_id,
                "status": r.status,
                "bonus_lines_count": r.bonus_lines_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
    }
