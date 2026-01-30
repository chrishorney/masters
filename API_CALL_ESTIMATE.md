# API Call Estimate (Final Optimized Version)

## Daily API Call Breakdown

### Automatic Sync (Background Job)
- **Frequency**: Every 5 minutes during active hours (6 AM - 11 PM CT = 17 hours)
- **Syncs per day**: 17 hours × 12 syncs/hour = **204 syncs/day**

### API Calls Per Sync

#### 1. Tournament Info
- **Calls**: 1 per sync
- **Daily total**: 204 calls

#### 2. Leaderboard
- **Calls**: 1 per sync
- **Daily total**: 204 calls

#### 3. Scorecards (Optimized Approach)

**Players with 2+ Stroke Improvement (Real-time detection)**
- **Logic**: Only fetches scorecards for players who improved by 2+ strokes compared to previous snapshot
- **Calls**: ~5-20 per sync (varies based on player performance)
- **Average**: ~10 calls per sync
- **Daily total**: 204 syncs × 10 = **2,040 calls**

**Manual Bonus Check (Admin Button)**
- **Frequency**: On-demand only (when admin clicks button)
- **Calls**: ~50-100 calls (all distinct entry players)
- **Daily total**: 0-100 calls (depends on usage)

**Scorecard daily total**: ~2,040 calls (automatic) + 0-100 calls (manual)

### Total Daily API Calls

**During Tournament Days (with automatic sync):**
- Tournament info: 204 calls
- Leaderboard: 204 calls
- Scorecards (2+ stroke): 2,040 calls
- Scorecards (manual check): 0-100 calls (on-demand)
- **Total: ~2,448 calls/day** (automatic only)
- **Total: ~2,548 calls/day** (with 1 manual check)

**On Non-Tournament Days:**
- Background job may not run (tournament not active)
- Manual syncs only: ~10-50 calls/day

## Monthly Estimate

**Tournament Week (4 days):**
- 4 days × 2,448 calls = **9,792 calls** (automatic only)
- With 1 manual check per day: 4 days × 2,548 calls = **10,192 calls**

**Rest of Month (26 days):**
- 26 days × 25 calls (manual syncs) = **650 calls**

**Monthly Total: ~10,500 calls/month** (automatic only)
**Monthly Total: ~11,000 calls/month** (with occasional manual checks)

## Benefits of This Approach

1. ✅ **Real-time detection**: Players with 2+ stroke improvements are detected immediately (every 5 minutes)
2. ✅ **Manual backup**: Admin can manually check all players when needed (catches missed bonuses)
3. ✅ **Efficient**: Only fetches scorecards when players improve significantly
4. ✅ **No scheduled overhead**: No automatic hourly syncs consuming API calls
5. ✅ **Reduces calls by ~90%** compared to fetching all entry players every sync

## How It Works

### Automatic Sync (Every 5 Minutes)
1. Fetches tournament info and leaderboard
2. Compares current leaderboard to previous snapshot
3. Identifies players who improved by 2+ strokes
4. Fetches scorecards for those players only
5. Recalculates bonuses and scores

### Manual Bonus Check (Admin Button)
1. Gets all distinct players from entries
2. Fetches scorecards for all entry players
3. Recalculates bonuses for all entries
4. Updates snapshot with merged scorecard data

## Recommendations

1. **Use automatic sync** for real-time updates during tournament play
2. **Use manual bonus check** if you suspect bonuses were missed (e.g., after reviewing scorecards)
3. **Monitor API usage** in logs to track actual calls
4. **Consider increasing sync interval** during non-peak hours (e.g., every 10 minutes instead of 5) to reduce calls further
