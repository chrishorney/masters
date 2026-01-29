# Setting Up a New Tournament

When a new tournament starts, follow these steps to point everything toward the new tournament.

## Quick Steps

1. **Sync the new tournament** (via Admin page or API)
2. **Upload new entries** for the new tournament
3. **Verify the frontend picks it up** (it should automatically)
4. **Optional: Update default tournament ID** in environment variables

---

## Detailed Instructions

### Step 1: Sync the New Tournament

The easiest way is through the Admin page:

1. Go to the **Admin** page
2. Navigate to the **"Tournament Management"** tab
3. In the **"Sync Tournament"** section, enter:
   - **Tournament Number** (e.g., "002", "470", etc.) - this is the `tourn_id` from the Slash Golf API
   - **Year** (e.g., 2026)
   - **Organization ID** (usually "1" for PGA Tour)
4. Click **"Sync Tournament"**

**Alternative: Using the API directly**

```bash
POST /api/tournament/sync?tourn_id=002&year=2026&org_id=1
```

**What this does:**
- Fetches tournament data from the Slash Golf API
- Creates or updates the tournament in the database
- Syncs all players from the leaderboard
- Creates the first score snapshot
- Sets the tournament as the "current" one (most recent by date)

---

### Step 2: Upload New Entries

1. Go to the **Admin** page
2. Navigate to the **"Entry Management"** tab
3. Click **"Choose File"** and select your entries CSV file
4. Click **"Upload Entries"**

**CSV Format:**
```csv
Participant Name,Player 1,Player 2,Player 3,Player 4,Player 5,Player 6
John Doe,Scottie Scheffler,Rory McIlroy,Jon Rahm,Viktor Hovland,Xander Schauffele,Collin Morikawa
Jane Smith,Tiger Woods,Phil Mickelson,Jordan Spieth,Justin Thomas,Brooks Koepka,Dustin Johnson
```

**Note:** Player names should match exactly as they appear in the tournament leaderboard.

---

### Step 3: Verify Frontend Display

The frontend automatically uses the **most recent tournament** (by year and start date) as the "current" tournament. After syncing the new tournament:

1. **Refresh the homepage** - it should show the new tournament name and dates
2. **Check the leaderboard** - it should show the new tournament's leaderboard
3. **Verify entries** - your new entries should appear

The system determines the "current" tournament by:
- Ordering tournaments by `year DESC, start_date DESC`
- Taking the first one (most recent)

So as long as your new tournament has a later start date than the previous one, it will automatically be the current tournament.

---

### Step 4: Optional - Update Default Tournament ID

If you want to update the default tournament ID for convenience (so you don't have to specify it every time), you can update your environment variables:

**In Railway (Production):**
1. Go to your Railway project
2. Navigate to **Variables** tab
3. Update:
   - `DEFAULT_TOURNAMENT_ID` = your new tournament number (e.g., "002")
   - `DEFAULT_YEAR` = current year (e.g., 2026)

**In local `.env` file:**
```env
DEFAULT_TOURNAMENT_ID=002
DEFAULT_YEAR=2026
```

**Note:** This is optional. The sync endpoint accepts tournament parameters directly, so you don't need to update defaults if you always specify them.

---

## Background Jobs (Automatic Sync)

If you have **automatic sync** enabled:

1. The background job will automatically sync the **current tournament** (most recent one)
2. It will calculate scores for the current tournament
3. No additional configuration needed - it picks up the new tournament automatically

**To verify automatic sync is working:**
- Go to Admin page → Tournament Management tab
- Check the "Background Job Status" section
- It should show the new tournament ID

---

## Troubleshooting

### Frontend still showing old tournament?

1. **Hard refresh** the browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Check that the new tournament was actually synced:
   ```bash
   GET /api/tournament/list
   ```
   This shows all tournaments. Verify your new one is there and has the latest start date.

### Can't find the tournament in the API?

1. Verify the tournament number (`tourn_id`) is correct
2. Check the year is correct
3. Try the API directly to see what tournaments are available:
   ```bash
   GET /api/tournament/list
   ```

### Entries not showing up?

1. Verify entries were uploaded for the correct tournament
2. Check that player names match exactly (case-sensitive)
3. Use the diagnostic endpoint to check:
   ```bash
   GET /api/admin/diagnostics/tournament/{tournament_id}
   ```

---

## Summary

**Minimum required steps:**
1. ✅ Sync new tournament (via Admin page or API)
2. ✅ Upload new entries

**That's it!** The frontend will automatically pick up the new tournament as the current one.

The system is designed to automatically use the most recent tournament, so you don't need to manually "switch" tournaments - just sync the new one and it becomes the current one.
