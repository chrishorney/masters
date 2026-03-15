# Bonus Points → Discord Validation

This document confirms that **all bonus points that are intended to be announced in real time** (hole-in-one, double eagle, eagle) are sent to Discord when they are awarded.

## Bonus types sent to Discord

Only these three bonus types are sent to Discord (by design):

- **hole_in_one**
- **double_eagle**
- **eagle**

Other bonus types (low_score, all_make_cut, gir_leader, fairways_leader) are not sent to Discord.

## Where bonuses are awarded

All **hole_in_one**, **double_eagle**, and **eagle** bonuses are created in exactly one place:

- **`ScoringService.calculate_and_save_daily_score()`** in `backend/app/services/scoring.py`

  - Bonus list comes from `calculate_bonus_points()` (scorecard-driven).
  - When persisting, we either **update** an existing `DailyScore` or **create** a new one.
  - In **both** branches we iterate over `bonuses` and, for each bonus that does **not** already exist in the DB, we:
    1. Create a `BonusPoint` record.
    2. Call **`_notify_discord_bonus_async(bonus, round_id, tournament)`**.
    3. Call `_notify_push_bonus_async(...)` for push.

So every **new** HIO/eagle/double_eagle that gets saved triggers a Discord notification.

## Callers of `calculate_and_save_daily_score`

Every path that can create these bonuses goes through this method:

| Caller | When | Discord? |
|--------|------|----------|
| **ScoreCalculatorService** (score calculation job) | Normal sync/calculate | Yes – same code path |
| **Admin “Bonus check”** (`/admin/bonus-check/check-all-players`) | Manual re-check of scorecards | Yes – uses same `ScoringService` |
| **Admin “Add bonus point”** (`/admin/bonus-points/add`) | Manual GIR/Fairways only | N/A – only allows `gir_leader` / `fairways_leader`, not HIO/eagle/double_eagle |

There is **no** other code path that creates `BonusPoint` records for hole_in_one, double_eagle, or eagle (import does not create these; admin add does not allow them).

## De-duplication

For a single run of scoring (one tournament/round), the same **golf shot** (e.g. player X, hole 5, eagle) can award a bonus to **multiple entries** that have that player. We only send **one** Discord message per (tournament, round, player, hole, bonus_type) via `_sent_discord_bonuses` in `ScoringService`. So:

- Every **new** HIO/eagle/double_eagle bonus that is **persisted** triggers Discord.
- We do not spam Discord when 10 entries all get the same eagle from one shot.

## Summary

- **All** hole_in_one, double_eagle, and eagle bonuses that are **newly** created are sent to Discord in real time through `_notify_discord_bonus_async` inside `calculate_and_save_daily_score`.
- The only way these bonuses are created is through `ScoringService.calculate_and_save_daily_score`, and both the “update existing daily score” and “create new daily score” branches call the Discord notifier when creating a new `BonusPoint` for those types.
- Automated tests (see `tests/test_bonus_discord_notification.py`) assert that creating such a bonus triggers the Discord notification.
