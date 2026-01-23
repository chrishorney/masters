# Tournament Data Fix Guide

This guide explains how to use the new diagnostic and fix tools for tournament data issues.

## Admin Endpoints

### 1. Run Diagnostics

Get a comprehensive report on tournament data integrity:

```bash
GET /api/admin/diagnostics/tournament/{tournament_id}
```

**Example:**
```bash
curl "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2"
```

**Response includes:**
- Tournament details
- Entry count and status
- Score snapshot information
- Daily scores breakdown
- Min Woo Lee detection (if in leaderboard)
- Issues and warnings
- Recommendations

### 2. Clear Tournament Data

Clear all scoring data for a tournament (keeps entries and players):

```bash
POST /api/admin/diagnostics/tournament/{tournament_id}/clear?confirm=true
```

**⚠️ WARNING: This is irreversible!**

**Example:**
```bash
curl -X POST "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2/clear?confirm=true"
```

**What gets deleted:**
- All daily scores
- All bonus points
- All ranking snapshots
- All score snapshots

**What is preserved:**
- Entries
- Players
- Tournament record

### 3. Auto-Fix Issues

Automatically fix common issues:

```bash
POST /api/admin/diagnostics/tournament/{tournament_id}/fix?recalculate_scores=true
```

**Example:**
```bash
curl -X POST "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2/fix?recalculate_scores=true"
```

**What it does:**
- Checks for common issues
- Recalculates scores if snapshots exist
- Provides fix summary

## Automated Fix Script

The `fix_tournament_data.py` script automates the entire fix process.

### Usage

```bash
cd backend
python fix_tournament_data.py --tournament-id 2 --api-url https://masters-production.up.railway.app
```

### Options

- `--tournament-id`: Tournament ID to fix (required)
- `--clear-all`: Clear all scoring data before fixing
- `--api-url`: API base URL (default: http://localhost:8000)
- `--skip-sync`: Skip tournament sync step
- `--skip-calculate`: Skip score calculation step

### Examples

**Full fix (clear, sync, calculate):**
```bash
python fix_tournament_data.py \
  --tournament-id 2 \
  --clear-all \
  --api-url https://masters-production.up.railway.app
```

**Just recalculate scores (if data is already synced):**
```bash
python fix_tournament_data.py \
  --tournament-id 2 \
  --skip-sync \
  --api-url https://masters-production.up.railway.app
```

**Diagnostics only (no fixes):**
```bash
python fix_tournament_data.py \
  --tournament-id 2 \
  --skip-sync \
  --skip-calculate \
  --api-url https://masters-production.up.railway.app
```

### What the Script Does

1. **Runs Diagnostics**: Checks current state of tournament data
2. **Clears Data** (if `--clear-all`): Removes all scoring data
3. **Syncs Tournament** (unless `--skip-sync`): Fetches latest data from API
4. **Calculates Scores** (unless `--skip-calculate`): Recalculates all scores
5. **Verifies Fix**: Runs diagnostics again to confirm issues are resolved

## Common Scenarios

### Scenario 1: Missing Scores

**Symptoms:**
- Entries exist but have no daily scores
- Leaderboard shows 0 points for all entries

**Fix:**
```bash
# Option 1: Just calculate scores (if snapshots exist)
python fix_tournament_data.py --tournament-id 2 --skip-sync --api-url https://masters-production.up.railway.app

# Option 2: Full fix (if snapshots are missing)
python fix_tournament_data.py --tournament-id 2 --clear-all --api-url https://masters-production.up.railway.app
```

### Scenario 2: Wrong Tournament Data

**Symptoms:**
- 2025 data showing instead of 2026
- Players from wrong year in leaderboard

**Fix:**
```bash
# Clear everything and rebuild
python fix_tournament_data.py --tournament-id 2 --clear-all --api-url https://masters-production.up.railway.app
```

### Scenario 3: Player Not in Leaderboard

**Symptoms:**
- Entry has player X
- Player X is in first place
- But entry doesn't show on leaderboard

**Fix:**
```bash
# First, check diagnostics
curl "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2"

# If player is missing from snapshot, re-sync
python fix_tournament_data.py --tournament-id 2 --clear-all --api-url https://masters-production.up.railway.app
```

### Scenario 4: Stale Data

**Symptoms:**
- Scores haven't updated
- Leaderboard is outdated

**Fix:**
```bash
# Re-sync and recalculate
python fix_tournament_data.py --tournament-id 2 --api-url https://masters-production.up.railway.app
```

## Step-by-Step Manual Process

If you prefer to do it manually:

1. **Check current state:**
   ```bash
   curl "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2"
   ```

2. **Clear data (if needed):**
   ```bash
   curl -X POST "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2/clear?confirm=true"
   ```

3. **Sync tournament:**
   ```bash
   curl -X POST "https://masters-production.up.railway.app/api/tournament/sync?year=2026"
   ```

4. **Calculate scores:**
   ```bash
   curl -X POST "https://masters-production.up.railway.app/api/scores/calculate-all?tournament_id=2"
   ```

5. **Verify:**
   ```bash
   curl "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2"
   ```

## Verification Checklist

After running fixes, verify:

- [ ] Tournament exists and has correct year
- [ ] Current round is correct
- [ ] Score snapshots exist
- [ ] Latest snapshot has leaderboard data
- [ ] All entries have daily scores
- [ ] Leaderboard shows correct points
- [ ] Min Woo Lee (or other specific player) appears correctly

## Troubleshooting

### Error: "Tournament not found"
- Check tournament ID is correct
- Verify tournament exists in database

### Error: "No score snapshots found"
- Run tournament sync first
- Check API is returning data

### Error: "No entries found"
- Verify entries are imported
- Check entries have correct tournament_id

### Scores still wrong after fix
- Check if entries have correct player IDs
- Verify player IDs match leaderboard snapshot
- Check if rebuy logic is correct

## Safety Features

- **Confirmation required**: Clear operation requires `confirm=true`
- **Preserves entries**: Entries and players are never deleted
- **Read-only diagnostics**: Diagnostics endpoint is safe to run anytime
- **Detailed logging**: All operations provide detailed output

## Next Steps

After fixing data:

1. Monitor automatic sync (if enabled)
2. Check leaderboard displays correctly
3. Verify specific entries show correct points
4. Test entry detail pages
