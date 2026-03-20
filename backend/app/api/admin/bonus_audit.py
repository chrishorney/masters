"""Admin API: bonus audit snapshots (scorecard-based, stored for reconciliation)."""
import logging
from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import (
    BonusAuditRun,
    BonusAuditLine,
    BonusPoint,
    DailyScore,
    Entry,
    ScoreSnapshot,
    Tournament,
)
from app.services.bonus_audit_service import run_bonus_audit
from app.services.scoring import ScoringService

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


def _line_key(
    entry_id: int,
    bonus_type: str,
    player_id: Optional[str],
    hole: Optional[int],
) -> Tuple[int, str, Optional[str], Optional[int]]:
    return (entry_id, bonus_type, str(player_id) if player_id is not None else None, hole)


def _audit_and_live_maps(
    db: Session, run: BonusAuditRun
) -> Tuple[Dict[Tuple[int, str, Optional[str], Optional[int]], BonusAuditLine], Dict[Tuple[int, str, Optional[str], Optional[int]], BonusPoint]]:
    audit_map: Dict[Tuple[int, str, Optional[str], Optional[int]], BonusAuditLine] = {}
    for line in run.lines:
        key = _line_key(line.entry_id, line.bonus_type, line.player_id, line.hole)
        # Keep first line for key; duplicates should be rare and keying intentionally matches BonusPoint uniqueness semantics.
        if key not in audit_map:
            audit_map[key] = line

    entry_ids = sorted({line.entry_id for line in run.lines})
    live_map: Dict[Tuple[int, str, Optional[str], Optional[int]], BonusPoint] = {}
    if entry_ids:
        live_rows = db.query(BonusPoint).filter(
            BonusPoint.round_id == run.round_id,
            BonusPoint.entry_id.in_(entry_ids),
        ).all()
        for bp in live_rows:
            key = _line_key(bp.entry_id, bp.bonus_type, bp.player_id, bp.hole)
            if key not in live_map:
                live_map[key] = bp
    return audit_map, live_map


def _recalculate_daily_scores_from_live_bonus_points(
    db: Session,
    tournament: Tournament,
    round_id: int,
    entry_ids: Set[int],
) -> int:
    """Recompute DailyScore totals for affected entries using current live BonusPoint rows."""
    if not entry_ids:
        return 0

    snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament.id,
        ScoreSnapshot.round_id == round_id,
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    if not snapshot:
        raise ValueError(f"No snapshot found for tournament {tournament.id}, round {round_id}.")

    leaderboard_data = snapshot.leaderboard_data or {}
    scoring = ScoringService(db)
    score_date = tournament.start_date
    if round_id > 1:
        score_date = date.fromordinal(tournament.start_date.toordinal() + (round_id - 1))

    updated = 0
    for entry_id in entry_ids:
        entry = db.query(Entry).filter(Entry.id == entry_id).first()
        if not entry:
            continue

        base = scoring.calculate_daily_base_points(entry, leaderboard_data, round_id, tournament)
        live_bonuses = db.query(BonusPoint).filter(
            BonusPoint.entry_id == entry.id,
            BonusPoint.round_id == round_id,
        ).all()
        bonus_total = float(sum(float(b.points or 0.0) for b in live_bonuses))
        total_points = float(base["total_points"]) + bonus_total

        details_bonus = [
            {
                "player_id": str(b.player_id) if b.player_id is not None else None,
                "bonus_type": b.bonus_type,
                "points": float(b.points),
                "hole": b.hole,
            }
            for b in live_bonuses
        ]

        score = db.query(DailyScore).filter(
            DailyScore.entry_id == entry.id,
            DailyScore.round_id == round_id,
        ).first()
        if score:
            score.base_points = float(base["total_points"])
            score.bonus_points = bonus_total
            score.total_points = total_points
            score.details = {
                "base_breakdown": base["breakdown"],
                "bonuses": details_bonus,
            }
        else:
            db.add(
                DailyScore(
                    entry_id=entry.id,
                    round_id=round_id,
                    date=score_date,
                    base_points=float(base["total_points"]),
                    bonus_points=bonus_total,
                    total_points=total_points,
                    details={
                        "base_breakdown": base["breakdown"],
                        "bonuses": details_bonus,
                    },
                )
            )
        updated += 1
    return updated


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


@router.get("/bonus-audit/reconcile/preview")
async def preview_bonus_audit_reconcile(
    run_id: int = Query(..., description="Bonus audit run ID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Preview differences between one audit run and live bonus_points."""
    run = (
        db.query(BonusAuditRun)
        .options(joinedload(BonusAuditRun.lines))
        .filter(BonusAuditRun.id == run_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")

    audit_map, live_map = _audit_and_live_maps(db, run)
    missing_keys = [k for k in audit_map.keys() if k not in live_map]
    extra_live_keys = [k for k in live_map.keys() if k not in audit_map]

    point_mismatches: List[Dict[str, Any]] = []
    for key in audit_map.keys():
        if key in live_map:
            audit_pts = float(audit_map[key].points or 0.0)
            live_pts = float(live_map[key].points or 0.0)
            if abs(audit_pts - live_pts) > 0.0001:
                line = audit_map[key]
                point_mismatches.append({
                    "entry_id": line.entry_id,
                    "participant_name": line.participant_name,
                    "player_id": line.player_id,
                    "player_name": line.player_name,
                    "bonus_type": line.bonus_type,
                    "hole": line.hole,
                    "audit_points": audit_pts,
                    "live_points": live_pts,
                })

    missing_lines = [_serialize_line(audit_map[k]) for k in missing_keys]
    extra_live_lines = [
        {
            "entry_id": live_map[k].entry_id,
            "player_id": str(live_map[k].player_id) if live_map[k].player_id is not None else None,
            "bonus_type": live_map[k].bonus_type,
            "points": float(live_map[k].points or 0.0),
            "hole": live_map[k].hole,
        }
        for k in extra_live_keys
    ]

    return {
        "success": True,
        "run": _serialize_run(run, include_lines=False),
        "summary": {
            "audit_lines": len(audit_map),
            "live_lines": len(live_map),
            "missing_in_live_count": len(missing_lines),
            "extra_in_live_count": len(extra_live_lines),
            "point_mismatch_count": len(point_mismatches),
        },
        "missing_in_live": missing_lines,
        "extra_in_live": extra_live_lines,
        "point_mismatches": point_mismatches,
    }


@router.post("/bonus-audit/reconcile/apply")
async def apply_bonus_audit_reconcile(
    run_id: int = Query(..., description="Bonus audit run ID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Apply audit differences to live bonus_points:
    - insert bonus rows present in audit but missing in live
    - update point value for rows with key match but different points
    - recalculate DailyScore for affected entries (round in this run)
    """
    run = (
        db.query(BonusAuditRun)
        .options(joinedload(BonusAuditRun.lines))
        .filter(BonusAuditRun.id == run_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    if run.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed audit runs can be reconciled")

    tournament = db.query(Tournament).filter(Tournament.id == run.tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found for audit run")

    audit_map, live_map = _audit_and_live_maps(db, run)
    added = 0
    updated = 0
    affected_entries: Set[int] = set()

    try:
        for key, line in audit_map.items():
            existing = live_map.get(key)
            if not existing:
                db.add(
                    BonusPoint(
                        entry_id=line.entry_id,
                        round_id=run.round_id,
                        bonus_type=line.bonus_type,
                        points=float(line.points),
                        player_id=str(line.player_id) if line.player_id is not None else None,
                        hole=line.hole,
                    )
                )
                added += 1
                affected_entries.add(line.entry_id)
            else:
                audit_pts = float(line.points or 0.0)
                live_pts = float(existing.points or 0.0)
                if abs(audit_pts - live_pts) > 0.0001:
                    existing.points = audit_pts
                    updated += 1
                    affected_entries.add(existing.entry_id)

        score_updates = _recalculate_daily_scores_from_live_bonus_points(
            db=db,
            tournament=tournament,
            round_id=run.round_id,
            entry_ids=affected_entries,
        )

        db.commit()
        return {
            "success": True,
            "run_id": run_id,
            "round_id": run.round_id,
            "bonus_points_added": added,
            "bonus_points_updated": updated,
            "entries_recalculated": score_updates,
            "message": (
                f"Reconciliation applied for run #{run_id}: "
                f"added {added}, updated {updated}, recalculated {score_updates} entries."
            ),
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.exception("Failed to apply audit reconciliation")
        raise HTTPException(status_code=500, detail=str(e))
