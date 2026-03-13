# Quick Diagnostic: Missing Tournament Data

## Step 1: Check API Endpoint

Run this command to see if the API can find a tournament:

```bash
curl https://masters-production.up.railway.app/api/tournament/current
```

**If you get 404**: Tournament data is missing from database
**If you get 500**: Database connection issue
**If you get 200**: Tournament exists, issue is with frontend

## Step 2: List All Tournaments

Check if ANY tournaments exist:

```bash
curl https://masters-production.up.railway.app/api/tournament/list
```

This will show all tournaments, even if they're not "current".

## Step 3: Check Railway Logs

1. Go to Railway dashboard
2. Check logs for:
   - Connection pool errors
   - Database connection errors
   - Any errors around the time you refreshed

## Most Likely Causes

### 1. Connection Pool Issue (Recent Changes)
The connection pool changes we just made might have caused a temporary issue.

**Solution**: Restart Railway service

### 2. Tournament Data Was Cleared
Someone or something called the clear-all endpoint.

**Solution**: Re-sync tournament data via admin page

### 3. Database Connection Lost
The database URL might be incorrect or connection was lost.

**Solution**: Check Railway environment variables for `DATABASE_URL`

## Quick Fix: Re-sync Tournament

If tournament data is missing:

1. Go to `/admin` page
2. Use "Tournament Management" tab
3. Fill in:
   - Year: `2026`
   - Tournament ID: `470` (or your tournament number)
   - Org ID: `1`
4. Click "Sync Tournament"
5. Import entries if needed
6. Calculate scores if needed
