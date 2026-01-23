# Round Display Debugging Guide

## Issue: Frontend Showing Round 1 When API Shows Round 2

### Root Cause Analysis

The frontend was showing Round 1 because:

1. **Database State**: The database has `current_round: 1` stored
2. **API State**: The Slash Golf API is currently returning `currentRound: {"$numberInt": "1"}`
3. **Frontend Cache**: React Query was caching tournament data for 5 minutes

### Current Status

**Database**: `current_round: 1`  
**API Raw Data**: `{"$numberInt": "1"}`  
**Frontend Display**: Round 1 (matches database)

**Conclusion**: The database is correctly storing what the API returns. If the API shows Round 2, a sync needs to be run to update the database.

---

## How to Check Current Round

### 1. Check Database Value

```bash
curl https://masters-production.up.railway.app/api/tournament/current | jq '.current_round'
```

### 2. Check Raw API Data

```bash
curl https://masters-production.up.railway.app/api/validation/api-raw | jq '{database_current_round, api_data_currentRound}'
```

### 3. Check Sync Status

```bash
curl https://masters-production.up.railway.app/api/validation/sync-status | jq '.tournament.current_round'
```

---

## How to Update Current Round

### Option 1: Manual Sync (Admin Page)

1. Go to `/admin` page
2. Click "Tournament Management" tab
3. Click "Sync Tournament" button
4. Wait for sync to complete
5. Refresh the page

### Option 2: API Sync Endpoint

```bash
curl -X POST "https://masters-production.up.railway.app/api/tournament/sync?org_id=1&tourn_id=002&year=2026"
```

### Option 3: Background Job (Automatic)

If background jobs are running, they will automatically sync every 5 minutes during active hours.

---

## Frontend Cache Improvements

### Changes Made

1. **Reduced staleTime**: From 5 minutes to 30 seconds
2. **Added refetchInterval**: Tournament data now refreshes every 60 seconds
3. **Auto-refresh**: Frontend will automatically fetch new data when rounds change

### Cache Behavior

- **staleTime: 30 seconds**: Data is considered fresh for 30 seconds
- **refetchInterval: 60 seconds**: Automatically refetch every minute
- **On Navigation**: Data refetches if stale when navigating between pages

---

## Troubleshooting Steps

### If Frontend Shows Wrong Round:

1. **Check Database**:
   ```bash
   curl https://masters-production.up.railway.app/api/tournament/current | jq '.current_round'
   ```

2. **Check API Raw Data**:
   ```bash
   curl https://masters-production.up.railway.app/api/validation/api-raw | jq '.api_data_currentRound'
   ```

3. **If Database is Wrong**:
   - Run sync: `curl -X POST "https://masters-production.up.railway.app/api/tournament/sync?org_id=1&tourn_id=002&year=2026"`
   - Wait 2-3 seconds
   - Check database again

4. **If Database is Correct but Frontend is Wrong**:
   - Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
   - Wait up to 60 seconds for auto-refresh
   - Or navigate to a different page and back

---

## Expected Behavior

### When Round Changes:

1. **API Updates**: Slash Golf API updates `currentRound` field
2. **Sync Runs**: Background job or manual sync fetches new data
3. **Database Updates**: `tournaments.current_round` is updated
4. **Frontend Refreshes**: 
   - Within 60 seconds (auto-refresh)
   - Or immediately on page navigation (if stale)

### Round Display Locations:

- ✅ **HomePage**: Shows `Round {tournament.current_round}`
- ✅ **LeaderboardPage**: Shows `Round {tournamentInfo.current_round}`
- ✅ **EntryDetailPage**: Shows `Round {tournament.current_round}` and marks current round
- ✅ **AdminPage**: Shows `Round {tournament.current_round}`
- ✅ **Layout**: Shows `Round {tournament.current_round}` in navigation

---

## Verification Checklist

- [ ] Database `current_round` matches API `currentRound`
- [ ] Frontend displays correct round
- [ ] Round updates within 60 seconds of database update
- [ ] All pages show consistent round number
- [ ] "(Current)" indicator shows next to active round

---

## Notes

- The frontend cache was the main issue (5 minutes was too long)
- Now reduced to 30 seconds with 60-second auto-refresh
- Database always reflects what the API returns
- If API shows Round 2 but database shows Round 1, sync needs to run

---

*Last Updated: January 2026*
