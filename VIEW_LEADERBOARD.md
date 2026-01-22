# View Leaderboard Instructions

## Quick Start

The E2E test created 2 test entries with real tournament data. Here's how to view them:

## 1. Start Backend (if not running)

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: http://localhost:8000

## 2. Start Frontend (if not running)

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:5173

## 3. View Leaderboard

Open your browser and go to:

**http://localhost:5173/leaderboard**

You should see:

### Current Leaderboard

1. **Test User 1** - **60.0 points**
   - Base Points: 55.0
   - Bonus Points: 5.0 (All 6 players made cut)
   - Players: Sepp Straka (1st), Justin Thomas (2nd), Justin Lower (T3), Jason Day (T3), Patrick Cantlay (T5), Charley Hoffman (T5)

2. **Test User 2** - **32.0 points**
   - Base Points: 26.0
   - Bonus Points: 6.0
   - Players: Camilo Villegas (T7), Taylor Moore (T7), Ben Griffin (T7), Max Greyserman (T7), Alex Smalley (11th), Nick Taylor (T12)

## 4. View Entry Details

Click on any entry name to see detailed breakdown:
- Individual player scores
- Round-by-round breakdown
- Bonus points earned
- Player positions

Or visit directly:
- Entry 1: http://localhost:5173/entry/5
- Entry 2: http://localhost:5173/entry/6

## 5. Test API Directly

You can also test the API directly:

```bash
curl "http://localhost:8000/api/scores/leaderboard?tournament_id=1" | python -m json.tool
```

Or visit the API docs:
- http://localhost:8000/docs

## What You'll See

The leaderboard shows:
- ✅ Real tournament data (The American Express)
- ✅ Calculated scores based on actual player positions
- ✅ Bonus points (All 6 make cut bonus)
- ✅ Ranked by total points
- ✅ Auto-refreshes every 30 seconds

## Troubleshooting

**Backend not responding?**
- Check if uvicorn is running: `ps aux | grep uvicorn`
- Check logs for errors
- Verify database connection

**Frontend not loading?**
- Check if npm dev server is running: `ps aux | grep vite`
- Check browser console for errors
- Verify `VITE_API_URL` in frontend/.env is `http://localhost:8000`

**No data showing?**
- Verify tournament exists: Check http://localhost:8000/api/tournament/current
- Verify entries exist: Check database or API
- Check browser network tab for API errors

## Next Steps

1. **Sync Latest Data**: Use admin dashboard to sync tournament again
2. **Add More Entries**: Import more entries via admin
3. **Test Manual Bonuses**: Add GIR/Fairways bonuses
4. **View Real-time Updates**: Leaderboard auto-refreshes every 30s
