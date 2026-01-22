# Post-Deployment Checklist

Your application is now live! Here's what to do next to get it ready for the tournament.

## ✅ Deployment Complete

**Backend:** `https://masters-production.up.railway.app`  
**Frontend:** `https://masters-livid.vercel.app`  
**Status:** ✅ Both services running and connected

---

## Step 1: Test Core Features (15 minutes)

### 1.1 Test Admin Dashboard
1. Visit: `https://masters-livid.vercel.app/admin`
2. Verify you can access all admin tabs:
   - ✅ Import Section
   - ✅ Bonus Points Section
   - ✅ Tournament Management Section

### 1.2 Test Tournament Sync
1. Go to Admin → Tournament Management
2. Click **"Sync Tournament Data"**
3. Enter tournament details (e.g., org_id: `1`, tourn_id: `002`, year: `2026`)
4. Verify it syncs successfully
5. Check that tournament appears on home page

### 1.3 Test Score Calculation
1. After syncing a tournament, click **"Calculate All Scores"**
2. Verify scores are calculated
3. Check leaderboard shows entries (even if empty)

### 1.4 Test Frontend Pages
- ✅ Home page loads tournament info
- ✅ Leaderboard page displays (even if empty)
- ✅ Entry detail pages work (when entries exist)

---

## Step 2: Import Real Data (30 minutes)

### 2.1 Prepare Your Data
1. Export entries from SmartSheet as CSV
2. Export rebuys from SmartSheet as CSV
3. Ensure CSV format matches expected format (see `docs/SMARTSHEET_FORMAT.md`)

### 2.2 Import Entries
1. Go to Admin → Import Section
2. Select **"Entries"** type
3. Upload your entries CSV file
4. Review import results
5. Fix any errors (player name mismatches, etc.)

### 2.3 Import Rebuys
1. Select **"Rebuys"** type
2. Upload your rebuys CSV file
3. Review import results
4. Verify rebuys are associated with correct entries

### 2.4 Verify Data
1. Check leaderboard shows all entries
2. Verify entry details show correct players
3. Check rebuy information is correct

---

## Step 3: Set Up First Tournament (10 minutes)

### 3.1 Sync Current Tournament
1. Identify the tournament you want to track
2. Get tournament details:
   - Organization ID (usually `1`)
   - Tournament ID (e.g., `002` for The American Express)
   - Year (e.g., `2026`)
3. Sync tournament data via Admin dashboard

### 3.2 Calculate Initial Scores
1. After sync, click **"Calculate All Scores"**
2. Verify scores appear in leaderboard
3. Check entry detail pages show correct points

### 3.3 Test Real-time Updates
1. Wait 30 seconds (frontend auto-refreshes)
2. Verify update indicator appears
3. Check that scores update automatically

---

## Step 4: Configure Manual Bonus Points (As Needed)

### 4.1 Add GIR Leader Bonus
1. Go to Admin → Bonus Points
2. Select round, bonus type: "GIR Leader"
3. Search and select player
4. Add bonus point

### 4.2 Add Fairways Hit Leader Bonus
1. Select round, bonus type: "Fairways Hit Leader"
2. Search and select player
3. Add bonus point

### 4.3 Verify Bonus Points
1. Check entry detail pages show bonus points
2. Verify total scores include bonus points

---

## Step 5: Share with Participants (5 minutes)

### 5.1 Share Leaderboard URL
- **Public URL:** `https://masters-livid.vercel.app/leaderboard`
- Share this with all participants

### 5.2 Share Admin Access (Optional)
- Only share admin URL with trusted administrators
- **Admin URL:** `https://masters-livid.vercel.app/admin`

---

## Step 6: Monitor First Tournament (Ongoing)

### 6.1 During Tournament
- Monitor Railway logs for any errors
- Check Vercel deployment status
- Verify scores update correctly after each round

### 6.2 Daily Tasks
- Sync tournament data (if not automated)
- Calculate scores after each round
- Add manual bonus points as needed
- Verify leaderboard accuracy

### 6.3 Troubleshooting
- If scores don't update, manually trigger calculation
- If data seems wrong, re-sync tournament
- Check browser console for errors
- Review Railway/Vercel logs

---

## Step 7: Optional Enhancements

### 7.1 Custom Domain
- Add custom domain in Vercel (e.g., `masters.yourdomain.com`)
- Update Railway CORS to include new domain
- Update Vercel `VITE_API_URL` if backend domain changes

### 7.2 Automated Sync (Future)
- Set up scheduled jobs to auto-sync tournament data
- Configure automatic score calculation
- Add email notifications for score updates

### 7.3 Additional Features
- Add user authentication (if needed)
- Implement email notifications
- Add tournament history
- Create mobile app version

---

## Quick Reference

### Important URLs
- **Frontend:** `https://masters-livid.vercel.app`
- **Backend API:** `https://masters-production.up.railway.app`
- **API Docs:** `https://masters-production.up.railway.app/docs`
- **Health Check:** `https://masters-production.up.railway.app/api/health`

### Admin Access
- **Admin Dashboard:** `https://masters-livid.vercel.app/admin`
- Use this to:
  - Import entries/rebuys
  - Add bonus points
  - Sync tournaments
  - Calculate scores

### Support
- Check logs in Railway dashboard
- Check logs in Vercel dashboard
- Review browser console for frontend errors
- See `PRODUCTION_DEPLOY.md` for troubleshooting

---

## 🎉 You're Ready!

Your application is fully deployed and ready to use. Start by importing your entries and syncing your first tournament!

**Next Action:** Import your entries CSV file via the Admin dashboard.
