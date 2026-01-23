# Round 2 Validation Guide

This guide helps you validate that all endpoints are correctly returning Round 2 data.

## Quick Validation

### Option 1: Using the Validation Script (Recommended)

```bash
# For local development
cd backend
python validate_round2.py --api-url http://localhost:8000

# For production
python validate_round2.py --api-url https://masters-production.up.railway.app
```

The script will check:
- ✅ Current round in database
- ✅ Latest snapshot round
- ✅ Round matches between database and snapshots
- ✅ Round 2 snapshot exists
- ✅ All endpoints return Round 2
- ✅ Entries have Round 2 scores

### Option 2: Using curl Commands

#### 1. Check Validation Endpoint
```bash
curl https://masters-production.up.railway.app/api/validation/sync-status | jq
```

**Expected Response:**
```json
{
  "tournament": {
    "current_round": 2,
    ...
  },
  "latest_snapshot": {
    "round_id": 2,
    ...
  },
  "validation": {
    "current_round_matches_latest_snapshot": true,
    ...
  }
}
```

#### 2. Check Current Tournament
```bash
curl https://masters-production.up.railway.app/api/tournament/current | jq
```

**Expected Response:**
```json
{
  "current_round": 2,
  "name": "The American Express",
  ...
}
```

#### 3. Check Leaderboard
```bash
# First get tournament ID
TOURNAMENT_ID=$(curl -s https://masters-production.up.railway.app/api/tournament/current | jq -r '.id')

# Then get leaderboard
curl "https://masters-production.up.railway.app/api/scores/leaderboard?tournament_id=$TOURNAMENT_ID" | jq '.tournament.current_round'
```

**Expected:** `2`

#### 4. Check Sync Response
After clicking "Sync Tournament" in the admin panel, check the response:

**Expected Response:**
```json
{
  "current_round": 2,
  "snapshot_round": 2,
  "scorecards_fetched": 0,
  ...
}
```

## What to Look For

### ✅ Correct Round 2 Indicators

1. **Database Round**: `tournament.current_round = 2`
2. **Snapshot Round**: Latest snapshot has `round_id = 2`
3. **Match**: `current_round_matches_latest_snapshot = true`
4. **Endpoints**: All endpoints return `current_round: 2`
5. **Scores**: Entries have `daily_scores` with `round_id: 2`

### ⚠️ Warning Signs

- `current_round` is 1, 3, or 4 (not 2)
- `current_round_matches_latest_snapshot = false`
- No Round 2 snapshot exists
- Entries missing Round 2 scores
- Different rounds in different endpoints

## Troubleshooting

### If Round is Not 2

1. **Check API Response**: The tournament API might still be returning Round 1
   - Verify the tournament is actually in Round 2
   - Check the Slash Golf API directly

2. **Force Sync**: Manually sync the tournament
   ```bash
   curl -X POST "https://masters-production.up.railway.app/api/tournament/sync?org_id=1&tourn_id=002&year=2026"
   ```

3. **Check Logs**: Look for sync log messages
   ```
   Successfully synced tournament The American Express - Round 2 (from API: 2)
   ```

### If Snapshots Don't Match

1. **Check Snapshot Round**: Verify latest snapshot is Round 2
   ```bash
   curl https://masters-production.up.railway.app/api/validation/sync-status | jq '.latest_snapshot.round_id'
   ```

2. **Check Database**: Verify tournament.current_round in database
   ```sql
   SELECT id, name, current_round FROM tournaments ORDER BY id DESC LIMIT 1;
   ```

### If Entries Missing Round 2 Scores

1. **Calculate Scores**: Run score calculation for Round 2
   ```bash
   TOURNAMENT_ID=$(curl -s https://masters-production.up.railway.app/api/tournament/current | jq -r '.id')
   curl -X POST "https://masters-production.up.railway.app/api/scores/calculate?tournament_id=$TOURNAMENT_ID&round_id=2"
   ```

## Frontend Validation

### Check Frontend Displays

1. **Home Page**: Should show "Round 2"
2. **Leaderboard Page**: Should show "Round 2" in header
3. **Entry Detail Page**: Should show "Round 2"
4. **Admin Page**: Should show "Round 2"

### Browser Console Check

Open browser DevTools (F12) → Console, then run:

```javascript
// Check current tournament
fetch('/api/tournament/current')
  .then(r => r.json())
  .then(data => console.log('Current Round:', data.current_round));

// Check leaderboard
fetch('/api/scores/leaderboard?tournament_id=1')
  .then(r => r.json())
  .then(data => console.log('Leaderboard Round:', data.tournament.current_round));
```

**Expected Output:**
```
Current Round: 2
Leaderboard Round: 2
```

## Automated Testing

You can also add this to your test suite:

```python
def test_round2_validation():
    """Test that Round 2 is correctly configured."""
    # Check validation endpoint
    response = client.get("/api/validation/sync-status")
    assert response.status_code == 200
    data = response.json()
    
    # Verify Round 2
    assert data["tournament"]["current_round"] == 2
    assert data["latest_snapshot"]["round_id"] == 2
    assert data["validation"]["current_round_matches_latest_snapshot"] == True
    
    # Check tournament endpoint
    response = client.get("/api/tournament/current")
    assert response.json()["current_round"] == 2
```

## Summary

The validation script provides a comprehensive check of all Round 2 data. Run it regularly to ensure:

- ✅ Database has correct round
- ✅ Snapshots match database
- ✅ All endpoints return consistent round
- ✅ Scores are calculated for Round 2
- ✅ Frontend displays correct round

---

*Last Updated: January 2026*
