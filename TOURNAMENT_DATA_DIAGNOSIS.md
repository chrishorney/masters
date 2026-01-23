# Tournament Data Integrity Diagnosis

## Problem
- Test user 1 has Min Woo Lee on their team
- Min Woo Lee is in first place in the tournament
- But Min Woo Lee doesn't appear on the leaderboard
- Suspected issue: 2025 data mixed with 2026 data

## Investigation Steps

### 1. Check Tournament IDs
- Tournament ID 1 = 2025 Masters
- Tournament ID 2 = 2026 Masters

### 2. Check Current Data State

Run these API calls to check the current state:

```bash
# Check tournament 2 (2026)
curl "https://masters-production.up.railway.app/api/tournament/2"

# Check tournament 1 (2025) for comparison
curl "https://masters-production.up.railway.app/api/tournament/1"

# Check leaderboard for tournament 2
curl "https://masters-production.up.railway.app/api/scores/leaderboard?tournament_id=2"

# Check latest score snapshot for tournament 2
curl "https://masters-production.up.railway.app/api/admin/players/tournament/2"
```

### 3. Common Issues and Fixes

#### Issue A: Entries Associated with Wrong Tournament
**Symptom**: Entries exist but have `tournament_id=1` instead of `tournament_id=2`

**Check**:
```sql
-- Check entries for tournament 2
SELECT id, participant_id, tournament_id, player1_id, player2_id 
FROM entries 
WHERE tournament_id = 2;

-- Check if any entries have wrong tournament_id
SELECT id, participant_id, tournament_id 
FROM entries 
WHERE tournament_id = 1 AND year = 2026;  -- This shouldn't exist
```

**Fix**: Update entries to correct tournament_id
```sql
-- Only if entries are wrong - BE CAREFUL!
UPDATE entries 
SET tournament_id = 2 
WHERE tournament_id = 1 
AND id IN (SELECT id FROM entries WHERE ...);  -- Add specific conditions
```

#### Issue B: Score Snapshots for Wrong Tournament
**Symptom**: Score snapshots exist but are associated with tournament_id=1

**Check**:
```sql
SELECT id, tournament_id, round_id, timestamp 
FROM score_snapshots 
ORDER BY timestamp DESC 
LIMIT 10;
```

**Fix**: Delete wrong snapshots and re-sync
```sql
-- Delete snapshots for tournament 1 (if they're actually 2026 data)
DELETE FROM score_snapshots WHERE tournament_id = 1;
```

#### Issue C: No Score Snapshots for Tournament 2
**Symptom**: No snapshots exist, so scoring can't work

**Fix**: Sync tournament data
```bash
curl -X POST "https://masters-production.up.railway.app/api/tournament/sync?year=2026"
```

#### Issue D: Scores Not Calculated
**Symptom**: Snapshots exist but no daily_scores

**Fix**: Calculate scores
```bash
# Calculate for current round
curl -X POST "https://masters-production.up.railway.app/api/scores/calculate?tournament_id=2"

# Or calculate all rounds
curl -X POST "https://masters-production.up.railway.app/api/scores/calculate-all?tournament_id=2"
```

#### Issue E: Player IDs Don't Match Leaderboard
**Symptom**: Entry has player_id but that player isn't in the leaderboard snapshot

**Check**: Compare entry player IDs with snapshot leaderboard
- Entry player IDs should match `playerId` in `leaderboardRows` of the snapshot

**Fix**: 
1. Re-sync tournament to get latest leaderboard
2. Verify player IDs are correct in entries

## Recommended Fix Process

### Option 1: Clean Slate (Recommended if data is corrupted)

1. **Clear all scoring data for tournament 2** (keeps entries and players):
   ```sql
   -- Delete daily scores
   DELETE FROM daily_scores 
   WHERE entry_id IN (SELECT id FROM entries WHERE tournament_id = 2);
   
   -- Delete bonus points
   DELETE FROM bonus_points 
   WHERE entry_id IN (SELECT id FROM entries WHERE tournament_id = 2);
   
   -- Delete ranking snapshots
   DELETE FROM ranking_snapshots 
   WHERE entry_id IN (SELECT id FROM entries WHERE tournament_id = 2);
   
   -- Delete score snapshots
   DELETE FROM score_snapshots WHERE tournament_id = 2;
   ```

2. **Verify entries are correct**:
   ```sql
   SELECT id, participant_id, tournament_id, 
          player1_id, player2_id, player3_id, 
          player4_id, player5_id, player6_id
   FROM entries 
   WHERE tournament_id = 2
   ORDER BY id;
   ```

3. **Re-sync tournament data**:
   ```bash
   curl -X POST "https://masters-production.up.railway.app/api/tournament/sync?year=2026"
   ```

4. **Calculate scores for all rounds**:
   ```bash
   curl -X POST "https://masters-production.up.railway.app/api/scores/calculate-all?tournament_id=2"
   ```

5. **Verify leaderboard**:
   ```bash
   curl "https://masters-production.up.railway.app/api/scores/leaderboard?tournament_id=2"
   ```

### Option 2: Targeted Fix (If only specific issues)

1. Check which specific issue exists using the diagnostic script
2. Fix only that issue
3. Re-sync and re-calculate as needed

## Verification Checklist

After fixing, verify:

- [ ] Tournament 2 exists and has correct year (2026)
- [ ] Tournament 2 has correct current_round
- [ ] All entries for tournament 2 have `tournament_id = 2`
- [ ] Score snapshots exist for tournament 2
- [ ] Latest snapshot has leaderboard data with players
- [ ] Min Woo Lee appears in latest snapshot leaderboard
- [ ] Entries with Min Woo Lee have daily_scores
- [ ] Leaderboard endpoint shows all entries with correct points
- [ ] Test user 1's entry appears on leaderboard with correct points

## Diagnostic Script

A Python script is available to check data integrity:

```bash
cd backend
python check_and_fix_tournament_data.py --tournament-id 2
```

To clear and rebuild:
```bash
python check_and_fix_tournament_data.py --tournament-id 2 --clear-all
```

## Next Steps

1. Run diagnostic to identify specific issues
2. Based on findings, either:
   - Use Option 1 (clean slate) if data is corrupted
   - Use Option 2 (targeted fix) if only specific issues
3. Verify all data is correct
4. Test leaderboard display
