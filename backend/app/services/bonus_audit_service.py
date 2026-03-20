"""Run scorecard-based bonus audits and persist snapshot rows for reconciliation."""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import (
    Tournament,
    Entry,
    Player,
    ScoreSnapshot,
    Participant,
    BonusAuditRun,
    BonusAuditLine,
)
from app.services.data_sync import DataSyncService
from app.services.scoring import ScoringService

logger = logging.getLogger(__name__)


def _player_display_name(db: Session, player_id: Optional[str]) -> Optional[str]:
    if not player_id:
        return None
    p = db.query(Player).filter(Player.player_id == str(player_id)).first()
    return p.full_name if p else str(player_id)


def _collect_entry_player_ids(entries: List[Entry], round_id: int) -> List[str]:
    """Distinct player IDs for all entries (main 6 + rebuys for R3–4)."""
    ids: set = set()
    for entry in entries:
        for field in (
            "player1_id",
            "player2_id",
            "player3_id",
            "player4_id",
            "player5_id",
            "player6_id",
        ):
            pid = getattr(entry, field, None)
            if pid:
                ids.add(str(pid))
        if round_id >= 3 and entry.rebuy_player_ids:
            for rid in entry.rebuy_player_ids:
                if rid:
                    ids.add(str(rid))
    return sorted(ids)


def run_bonus_audit(
    db: Session,
    tournament_id: int,
    round_id: int,
    trigger_source: str = "admin",
) -> Tuple[BonusAuditRun, List[Dict[str, Any]], List[str]]:
    """
    Fetch scorecards for all entry players, merge with latest snapshot for the round,
    compute bonuses per entry (same rules as ScoringService.calculate_bonus_points in audit_mode),
    and persist BonusAuditRun + BonusAuditLine rows.

    Returns:
        (run, summary_lines_for_api, errors)
    """
    errors: List[str] = []

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise ValueError(f"Tournament {tournament_id} not found")

    if not (1 <= round_id <= 4):
        raise ValueError("Round must be between 1 and 4")

    entries = (
        db.query(Entry)
        .filter(Entry.tournament_id == tournament_id)
        .all()
    )

    run = BonusAuditRun(
        tournament_id=tournament_id,
        round_id=round_id,
        status="running",
        trigger_source=trigger_source,
        players_checked=0,
        scorecards_fetched=0,
        entries_audited=len(entries),
        bonus_lines_count=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    run_id = run.id

    try:
        player_ids = _collect_entry_player_ids(entries, round_id)
        run.players_checked = len(player_ids)
        db.commit()

        api_lines: List[Dict[str, Any]] = []
        line_count = 0

        if not player_ids:
            run.status = "completed"
            run.bonus_lines_count = 0
            run.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(run)
            return run, [], []

        sync_service = DataSyncService(db)
        fetched: Dict[str, Any] = {}
        fetched_count = 0
        for pid in player_ids:
            try:
                scorecards = sync_service.api_client.get_scorecard(
                    player_id=pid,
                    org_id=tournament.org_id,
                    tourn_id=tournament.tourn_id,
                    year=tournament.year,
                )
                if not isinstance(scorecards, list):
                    fetched[pid] = [scorecards] if isinstance(scorecards, dict) else []
                else:
                    fetched[pid] = scorecards
                fetched_count += 1
            except Exception as e:
                msg = f"Failed to fetch scorecard for player {pid}: {e}"
                logger.warning(msg)
                errors.append(msg)

        run.scorecards_fetched = fetched_count
        db.commit()

        snapshot = (
            db.query(ScoreSnapshot)
            .filter(
                ScoreSnapshot.tournament_id == tournament_id,
                ScoreSnapshot.round_id == round_id,
            )
            .order_by(ScoreSnapshot.timestamp.desc())
            .first()
        )
        if not snapshot:
            raise ValueError(
                f"No score snapshot for tournament {tournament_id}, round {round_id}. Sync first."
            )

        leaderboard_data = snapshot.leaderboard_data or {}
        merged_scorecard_data: Dict[str, Any] = {}
        existing = snapshot.scorecard_data or {}
        for pid, sc in existing.items():
            merged_scorecard_data[str(pid)] = sc
        for pid, sc in fetched.items():
            if not isinstance(sc, list):
                sc = [sc] if isinstance(sc, dict) else []
            if sc:
                merged_scorecard_data[str(pid)] = sc

        scoring = ScoringService(db)

        for entry in entries:
            participant = (
                db.query(Participant).filter(Participant.id == entry.participant_id).first()
            )
            participant_name = participant.name if participant else f"Entry {entry.id}"

            bonuses = scoring.calculate_bonus_points(
                entry=entry,
                leaderboard_data=leaderboard_data,
                scorecard_data=merged_scorecard_data,
                round_id=round_id,
                tournament=tournament,
                audit_mode=True,
            )

            for b in bonuses:
                pid = b.get("player_id")
                if pid is not None:
                    pid = str(pid)
                display = _player_display_name(db, pid)
                line = BonusAuditLine(
                    run_id=run_id,
                    entry_id=entry.id,
                    participant_name=participant_name,
                    player_id=pid,
                    player_name=display,
                    bonus_type=b["bonus_type"],
                    points=float(b["points"]),
                    hole=b.get("hole"),
                )
                db.add(line)
                line_count += 1
                api_lines.append(
                    {
                        "entry_id": entry.id,
                        "participant_name": participant_name,
                        "player_id": pid,
                        "player_name": display,
                        "bonus_type": b["bonus_type"],
                        "points": float(b["points"]),
                        "hole": b.get("hole"),
                    }
                )

        run = db.query(BonusAuditRun).filter(BonusAuditRun.id == run_id).first()
        if run:
            run.bonus_lines_count = line_count
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run, api_lines, errors

    except Exception as e:
        logger.error("Bonus audit failed: %s", e, exc_info=True)
        db.rollback()
        run = db.query(BonusAuditRun).filter(BonusAuditRun.id == run_id).first()
        if run:
            run.status = "failed"
            run.error_message = str(e)[:4000]
            run.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(run)
        raise
