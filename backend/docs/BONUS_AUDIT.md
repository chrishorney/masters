# Bonus audit (scorecard snapshots)

The bonus audit is a **read-only snapshot** of what the scoring engine would award for bonuses for a given tournament round, based on:

- Fresh Slash Golf **scorecards** for every distinct player on entries (main six + rebuy players for rounds 3–4)
- The **latest `ScoreSnapshot`** for that tournament + round (for leaderboard-derived bonuses such as **low score of the round**)
- The same `ScoringService.calculate_bonus_points` rules as live scoring, with **`audit_mode=True`** so the entry’s `weekend_bonus_earned` flag is **not** updated

Results are stored in:

- `bonus_audit_runs` — one row per execution
- `bonus_audit_lines` — one row per detected bonus (eagle, HIO, low score, manual GIR/fairways pulled from DB, weekend loyalty when applicable, etc.)

This **does not** insert into `bonus_points` or recalculate `DailyScore`. It is intended for reconciliation and future scheduled comparisons against live data.

## Admin API

- `POST /api/admin/bonus-audit/run?tournament_id=&round_id=` — run audit and return lines in the response
- `GET /api/admin/bonus-audit/runs/{run_id}` — load a saved run and all lines
- `GET /api/admin/bonus-audit/runs?tournament_id=&round_id=&limit=` — list recent runs

## Admin UI

Tournament management → **Bonus audit (scorecard snapshot)** → **Run bonus audit & save snapshot**. Uses the same **Round** dropdown as “Check all players for bonuses.”

## Database migration

Apply Alembic revision `f1a2b3c4d5e6_add_bonus_audit_tables`.
