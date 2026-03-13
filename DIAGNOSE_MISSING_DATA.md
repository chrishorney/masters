# Diagnosing Missing Tournament Data

## Quick Checks

### 1. Check Database Directly

Run the diagnostic script:
```bash
cd backend
python3 check_database_state.py
```

This will show:
- How many tournaments exist
- How many entries exist
- Database connection status

### 2. Check API Endpoint

Test the current tournament endpoint:
```bash
curl https://masters-production.up.railway.app/api/tournament/current
```

Expected responses:
- **200 OK**: Tournament exists, returns tournament data
- **404 Not Found**: No tournament in database (this is the problem)

### 3. Check All Tournaments

List all tournaments:
```bash
curl https://masters-production.up.railway.app/api/tournament/list
```

This shows all tournaments in the database, even if they're not "current".

## Common Causes

### Scenario 1: Database Connection Issue
**Symptoms**: API returns 500 error or connection timeout

**Solution**: 
- Check Railway logs for connection errors
- Verify `DATABASE_URL` environment variable in Railway
- The connection pool changes we just made might need a restart

### Scenario 2: Tournament Data Was Cleared
**Symptoms**: API returns 404 "No tournament found"

**Possible causes**:
- Someone called `/api/admin/diagnostics/clear-all?confirm=true` (requires confirmation)
- Database was reset/migrated
- Railway database was restored from backup

**Solution**: Re-sync tournament data using admin page

### Scenario 3: Frontend Configuration Issue
**Symptoms**: Frontend shows error but API works

**Check**:
- Verify `VITE_API_URL` in Vercel environment variables
- Check browser console for API errors
- Verify frontend is pointing to correct backend URL

## Recovery Steps

### If Tournament Data is Missing:

1. **Go to Admin Page** (`/admin`)
2. **Navigate to "Tournament Management" tab**
3. **Use "Create/Sync Tournament" form**:
   - Year: `2026`
   - Tournament ID: `470` (or your tournament ID)
   - Org ID: `1`
4. **Click "Sync Tournament"**
5. **Import entries** (if needed)
6. **Calculate scores** (if needed)

### If Database Connection is Broken:

1. **Check Railway logs** for connection errors
2. **Verify DATABASE_URL** in Railway environment variables
3. **Restart Railway service** if needed
4. **Check Supabase** connection pool status

## Prevention

To prevent accidental data loss:

1. **Never call `/api/admin/diagnostics/clear-all`** without understanding the consequences
2. **Always require confirmation** (`confirm=true`) for destructive operations
3. **Backup database** before major operations
4. **Monitor Railway logs** for errors
