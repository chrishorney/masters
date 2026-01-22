# Quick Deployment Guide

Fast deployment steps for production.

## 1. Database (5 minutes)

1. Create Supabase project: https://supabase.com
2. Get connection string (use Connection Pooling format)
3. Run migrations:
   ```bash
   cd backend
   export DATABASE_URL="your_connection_string"
   alembic upgrade head
   ```

## 2. Backend (10 minutes)

### Railway (Recommended)

1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select your repo
4. Set environment variables:
   - `DATABASE_URL`
   - `SLASH_GOLF_API_KEY`
   - `SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com`
5. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Deploy!

### Render (Alternative)

1. Go to https://render.com
2. New Web Service
3. Connect GitHub repo
4. Build: `cd backend && pip install -r requirements.txt`
5. Start: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables (same as Railway)
7. Deploy!

## 3. Frontend (5 minutes)

1. Go to https://vercel.com
2. Add New Project
3. Import GitHub repo
4. Settings:
   - Framework: Vite
   - Root Directory: `frontend`
   - Build: `npm run build`
   - Output: `dist`
5. Environment Variable:
   - `VITE_API_URL=https://your-backend-url.railway.app`
6. Deploy!

## 4. Test (5 minutes)

1. Visit frontend URL
2. Go to `/admin`
3. Sync tournament
4. Import test entries
5. Verify leaderboard

## Done! 🎉

Your app is live. Total time: ~25 minutes.

## Troubleshooting

**Backend won't start?**
- Check `DATABASE_URL` is correct
- Verify port uses `$PORT` variable
- Check logs in Railway/Render dashboard

**Frontend can't connect?**
- Verify `VITE_API_URL` matches backend URL
- Check CORS is configured (should be automatic)
- Test backend directly: `https://your-backend-url/api/health`

**Database errors?**
- Run migrations: `alembic upgrade head`
- Verify connection string format
- Check Supabase project is active

## Next Steps

1. Add custom domain (optional)
2. Set up monitoring
3. Test with real tournament data
4. Train admin users
