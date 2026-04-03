#!/usr/bin/env python3
"""
Build rebuy .xlsx from valspar_entries_25.csv + Slash Golf leaderboards.json.

The PDF export is not machine-readable in this environment; leaderboards.json is
the same Valspar field (Innisbrook) with R2 CUT lines — good for import testing.

Usage (repo root):
  pip install openpyxl
  python3 scripts/build_valspar_rebuy_sample.py
"""
from __future__ import annotations

import csv
import json
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from openpyxl import Workbook
except ImportError:
    print("pip install openpyxl", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "valspar_entries_25.csv"
JSON_PATH = ROOT / "Slash Golf Jsons" / "leaderboards.json"
OUT_PATH = ROOT / "docs" / "samples" / "valspar_rebuy_sample_round2.xlsx"

# CSV typos -> spelling that exists on leaderboard JSON (for ranking + Replace with)
NAME_ALIASES = {
    "xander schuaffele": "Xander Schauffele",
    "jordan speith": "Jordan Spieth",
    "nicolai hojgaard": "Nicolai Højgaard",
}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def parse_position(pos) -> float:
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


def load_leaderboard(path: Path) -> List[Tuple[float, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("leaderboardRows") or []
    scored: List[Tuple[float, str]] = []
    seen: set[str] = set()
    for r in rows:
        first = (r.get("firstName") or "").strip()
        last = (r.get("lastName") or "").strip()
        full = f"{first} {last}".strip()
        if not full:
            continue
        pr = parse_position(r.get("position"))
        key = normalize(full)
        if key not in seen:
            scored.append((pr, full))
            seen.add(key)
    scored.sort(key=lambda x: (x[0], x[1]))
    return scored


def build_rank_by_norm(scored: List[Tuple[float, str]]) -> Dict[str, float]:
    return {normalize(full): pr for pr, full in scored}


def player_rank(raw: str, rank_by_norm: Dict[str, float]) -> float:
    raw_n = normalize(raw)
    if raw_n in NAME_ALIASES:
        raw_n = normalize(NAME_ALIASES[raw_n])
    return rank_by_norm.get(raw_n, 9999.0)


def replacement_pool(scored: List[Tuple[float, str]], roster_norms: set[str], limit: int = 45) -> List[str]:
    pool: List[str] = []
    for _pr, full in scored:
        if normalize(full) in roster_norms:
            continue
        pool.append(full)
        if len(pool) >= limit:
            break
    return pool


def rebuy_count(idx: int, n: int) -> int:
    if n <= 1:
        return 0
    p = idx / max(n - 1, 1)
    if p < 0.28:
        return 5
    if p < 0.52:
        return 3
    if p < 0.78:
        return 2
    if idx % 3 == 0:
        return 0
    return 1


def main() -> None:
    scored = load_leaderboard(JSON_PATH)
    rank_by_norm = build_rank_by_norm(scored)

    entries: List[Tuple[str, List[str], float]] = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pname = (row.get("Participant Name") or "").strip()
            if not pname:
                continue
            picks = [(row.get(f"Player {i} Name") or "").strip() for i in range(1, 7)]
            if len(picks) != 6 or not all(picks):
                continue
            ranks = [player_rank(p, rank_by_norm) for p in picks]
            weakness = sum(ranks) / 6.0
            entries.append((pname, picks, weakness))

    entries.sort(key=lambda x: x[2], reverse=True)
    n = len(entries)

    header = (
        ["Player Name"]
        + [f"Professional {i}" for i in range(1, 7)]
        + [x for _ in range(6) for x in ("Replace", "Replace with")]
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Rebuys"
    ws.append(header)

    for idx, (pname, picks, _weak) in enumerate(entries):
        roster_norms = {normalize(p) for p in picks}
        pool = list(replacement_pool(scored, roster_norms))
        k = rebuy_count(idx, n)

        # Replace worst-ranked golfers first (CSV spelling in "Replace" column)
        by_worst = sorted(picks, key=lambda p: player_rank(p, rank_by_norm), reverse=True)

        pairs: List[Tuple[str, str]] = []
        for orig in by_worst:
            if len(pairs) >= k:
                break
            while pool and normalize(pool[0]) == normalize(orig):
                pool.pop(0)
            if not pool:
                break
            rep = pool.pop(0)
            pairs.append((orig, rep))

        row_out: List[str] = [pname, *picks]
        for i in range(6):
            if i < len(pairs):
                row_out.extend([pairs[i][0], pairs[i][1]])
            else:
                row_out.extend(["", ""])
        ws.append(row_out)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_PATH)

    print(f"Wrote {OUT_PATH}")
    print(f"Entries: {n} | Source CSV: {CSV_PATH.name} | Leaderboard: {JSON_PATH.name}")
    print("Top of board (replacement pool):", ", ".join(f for _, f in scored[:8]))


if __name__ == "__main__":
    main()
