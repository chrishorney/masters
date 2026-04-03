#!/usr/bin/env python3
"""
Build SmartSheet-style rebuy .xlsx from YOUR database:
  - Every entry in the chosen tournament (original 6 golfers from DB / Player names)
  - Replace-with names from the TOP of the latest leaderboard snapshot (R2-friendly)

Run from repo root with backend deps and DATABASE_URL in backend/.env:

  cd /path/to/masters
  pip install -r backend/requirements.txt
  python3 scripts/build_rebuy_example_xlsx.py
  python3 scripts/build_rebuy_example_xlsx.py --tournament-id 3 --output ./rebuys.xlsx

This cannot read your production DB from Cursor; you run it locally (or on a server) where .env points at the real database.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DEFAULT_OUT = ROOT / "docs" / "samples" / "rebuy_example_mix.xlsx"

sys.path.insert(0, str(BACKEND))

try:
    from openpyxl import Workbook
except ImportError:
    print("Install openpyxl: pip install -r backend/requirements.txt", file=sys.stderr)
    sys.exit(1)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass


def position_rank(pos: Any) -> float:
    """Lower = better (leaderboard). CUT/WD/etc. = very bad."""
    if pos is None:
        return 9999.0
    s = str(pos).strip().upper()
    if s in ("", "-", "CUT", "WD", "DQ", "MDF", "DNS"):
        return 9998.0
    s = s.lstrip("T")
    try:
        return float(s)
    except ValueError:
        return 9997.0


def parse_leaderboard_rows(snapshot) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    """
    Returns (ordered list of {player_id, full_name, rank}, position_by_player_id).
    Order is best finish first (by parsed position).
    """
    data = snapshot.leaderboard_data or {}
    rows = data.get("leaderboardRows") or []
    enriched: List[Tuple[float, str, str]] = []
    pos_by_pid: Dict[str, float] = {}

    for r in rows:
        pid = str(r.get("playerId") or "").strip()
        if not pid:
            continue
        first = (r.get("firstName") or "").strip()
        last = (r.get("lastName") or "").strip()
        full = f"{first} {last}".strip() or pid
        pr = position_rank(r.get("position"))
        pos_by_pid[pid] = pr
        enriched.append((pr, pid, full))

    enriched.sort(key=lambda x: (x[0], x[1]))
    ordered = [{"player_id": pid, "full_name": full, "rank": pr} for pr, pid, full in enriched]
    return ordered, pos_by_pid


def pick_snapshot(db, tournament_id: int, prefer_round: Optional[int]) -> Any:
    from app.models import ScoreSnapshot

    q = (
        db.query(ScoreSnapshot)
        .filter(ScoreSnapshot.tournament_id == tournament_id)
        .order_by(ScoreSnapshot.timestamp.desc())
    )
    if prefer_round is not None:
        snap = q.filter(ScoreSnapshot.round_id == prefer_round).first()
        if snap:
            return snap
    return q.first()


def resolve_tournament(db, tournament_id: Optional[int]):
    from app.models import Tournament

    if tournament_id is not None:
        t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not t:
            raise SystemExit(f"Tournament id={tournament_id} not found.")
        return t
    # Prefer in-progress, else most recent by start_date
    t = (
        db.query(Tournament)
        .filter(Tournament.status.isnot(None))
        .filter(Tournament.status.ilike("%progress%"))
        .order_by(Tournament.start_date.desc())
        .first()
    )
    if t:
        return t
    t = db.query(Tournament).order_by(Tournament.start_date.desc()).first()
    if not t:
        raise SystemExit("No tournaments in database.")
    return t


def player_name_map(db) -> Dict[str, str]:
    from app.models import Player

    return {p.player_id: p.full_name for p in db.query(Player).all()}


def entry_player_ids(entry) -> List[str]:
    return [
        str(entry.player1_id),
        str(entry.player2_id),
        str(entry.player3_id),
        str(entry.player4_id),
        str(entry.player5_id),
        str(entry.player6_id),
    ]


def entry_display_names(entry, pid_to_name: Dict[str, str], lb_names: Dict[str, str]) -> List[str]:
    """Six names for Professional columns — prefer Player table, else leaderboard."""
    names: List[str] = []
    for pid in entry_player_ids(entry):
        nm = pid_to_name.get(pid) or lb_names.get(pid) or pid
        names.append(nm)
    return names


def compute_entry_strength(pos_by_pid: Dict[str, float], entry) -> float:
    """Average leaderboard position of the six picks (higher = weaker pool entry)."""
    pids = entry_player_ids(entry)
    ranks = [pos_by_pid.get(pid, 9999.0) for pid in pids]
    return sum(ranks) / max(len(ranks), 1)


def choose_rebuy_pairs(
    entry,
    display_names_by_pid: Dict[str, str],
    pos_by_pid: Dict[str, float],
    leaders_ordered: Sequence[Dict[str, Any]],
    num_pairs: int,
    max_leader_pool: int = 45,
) -> List[Tuple[str, str]]:
    """
    num_pairs replace pairs: drop worst-position golfers on this entry for the best
    available leaderboard names not already on the card.
    """
    pids = entry_player_ids(entry)
    pid_to_display = {pid: display_names_by_pid.get(pid, pid) for pid in pids}

    # Worst picks first (higher rank number = worse)
    sorted_pids = sorted(pids, key=lambda pid: pos_by_pid.get(pid, 9999.0), reverse=True)

    entry_pid_set = set(pids)
    leader_candidates: List[Dict[str, Any]] = []
    for L in leaders_ordered:
        if L["player_id"] in entry_pid_set:
            continue
        leader_candidates.append(L)
        if len(leader_candidates) >= max_leader_pool:
            break

    pairs: List[Tuple[str, str]] = []
    used_original_pids: set[str] = set()
    li = 0

    for orig_pid in sorted_pids:
        if len(pairs) >= num_pairs:
            break
        if orig_pid in used_original_pids:
            continue
        if li >= len(leader_candidates):
            break
        rep = leader_candidates[li]
        li += 1
        if rep["player_id"] == orig_pid:
            continue
        orig_name = pid_to_display.get(orig_pid, orig_pid)
        pairs.append((orig_name, rep["full_name"]))
        used_original_pids.add(orig_pid)

    return pairs


def rebuy_count_for_index(idx: int, n: int) -> int:
    """Spread rebuy intensity like a normal week: weak entries swap more; some leaders stand pat."""
    if n <= 0:
        return 0
    # idx 0 = weakest entry after sort
    p = idx / max(n - 1, 1)
    if p < 0.28:
        return min(5, 5)
    if p < 0.52:
        return 3
    if p < 0.78:
        return 2
    # Top ~22%: mix of 0 and 1 (every 3rd keeps full roster for weekend bonus)
    if idx % 3 == 0:
        return 0
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Build rebuy .xlsx from DB entries + leaderboard snapshot.")
    parser.add_argument("--tournament-id", type=int, default=None, help="Tournament PK (default: infer)")
    parser.add_argument(
        "--prefer-round",
        type=int,
        default=None,
        help="Prefer leaderboard snapshot for this round_id (default: tournament.current_round)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT, help="Output .xlsx path")
    args = parser.parse_args()

    _load_env()

    from app.database import SessionLocal
    from app.models import Entry, Participant

    db = SessionLocal()
    try:
        tournament = resolve_tournament(db, args.tournament_id)
        prefer_round = args.prefer_round
        if prefer_round is None:
            prefer_round = tournament.current_round

        snap = pick_snapshot(db, tournament.id, prefer_round)
        if not snap or not (snap.leaderboard_data or {}).get("leaderboardRows"):
            raise SystemExit(
                f"No leaderboard snapshot for tournament {tournament.id} ({tournament.name!r}). "
                "Sync scores / leaderboard from admin first."
            )

        leaders_ordered, pos_by_pid = parse_leaderboard_rows(snap)
        if not leaders_ordered:
            raise SystemExit("Leaderboard snapshot has no rows.")

        pid_to_name = player_name_map(db)
        lb_names = {L["player_id"]: L["full_name"] for L in leaders_ordered}

        entries = (
            db.query(Entry)
            .filter(Entry.tournament_id == tournament.id)
            .order_by(Entry.id)
            .all()
        )
        if not entries:
            raise SystemExit(f"No entries for tournament {tournament.id}.")

        # Merge snapshot positions with any player on entries missing from this snap
        for e in entries:
            for pid in entry_player_ids(e):
                if pid not in pos_by_pid:
                    pos_by_pid[pid] = 9999.0

        # Strength = average position; sort ascending strength = weakest entries first
        scored: List[Tuple[float, Any]] = []
        for e in entries:
            strength = compute_entry_strength(pos_by_pid, e)
            scored.append((strength, e))
        scored.sort(key=lambda x: x[0], reverse=True)

        dup_names = [n for n, c in Counter(e.participant.name for e in entries).items() if c > 1]
        if dup_names:
            print(
                "WARNING: duplicate Participant names in this tournament — rebuy import uses .first() match:",
                ", ".join(dup_names),
                file=sys.stderr,
            )

        header = (
            ["Player Name"]
            + [f"Professional {i}" for i in range(1, 7)]
            + [x for _ in range(6) for x in ("Replace", "Replace with")]
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "Rebuys"
        ws.append(header)

        n = len(scored)
        for idx, (_strength, entry) in enumerate(scored):
            participant = db.query(Participant).filter(Participant.id == entry.participant_id).first()
            pname = participant.name if participant else f"Participant {entry.participant_id}"
            prof_names = entry_display_names(entry, pid_to_name, lb_names)
            display_by_pid = {pid: nm for pid, nm in zip(entry_player_ids(entry), prof_names)}

            k = rebuy_count_for_index(idx, n)
            pairs = choose_rebuy_pairs(entry, display_by_pid, pos_by_pid, leaders_ordered, k)

            row_out: List[str] = [pname, *prof_names]
            for i in range(6):
                if i < len(pairs):
                    row_out.extend([pairs[i][0], pairs[i][1]])
                else:
                    row_out.extend(["", ""])
            ws.append(row_out)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        wb.save(args.output)

        top5 = ", ".join(L["full_name"] for L in leaders_ordered[:5])
        print(f"Tournament: {tournament.name} (id={tournament.id}, year={tournament.year})")
        print(f"Snapshot: round_id={snap.round_id}, timestamp={snap.timestamp}")
        print(f"Entries: {n} | Prefer-round filter: {prefer_round!r} (fallback to latest if no match)")
        print(f"Top of board used for replacements (sample): {top5}")
        print(f"Wrote {args.output.resolve()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
