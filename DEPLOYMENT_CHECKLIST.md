# Production Deployment Checklist

Use this checklist to track your deployment progress.

## Pre-Deployment ✅
- [x] All code committed to git
- [x] All features tested locally
- [x] Database migrations ready
- [ ] GitHub repository created (if not already)
- [ ] Code pushed to GitHub

## Step 1: Database (Supabase)
- [ ] Create Supabase account
- [ ] Create new project
- [ ] Get connection string (Connection Pooling format)
- [ ] Run migrations: `alembic upgrade head`
- [ ] Test connection

## Step 2: Backend (Railway)
- [ ] Create Railway account
- [ ] Connect GitHub repository
- [ ] Create new project
- [ ] Configure service (root: `backend`, start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
- [ ] Set environment variables:
  - [ ] `DATABASE_URL`
  - [ ] `SLASH_GOLF_API_KEY`
  - [ ] `SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com`
  - [ ] `API_PREFIX=/api`
  - [ ] `ENVIRONMENT=production`
  - [ ] `LOG_LEVEL=INFO`
- [ ] Deploy backend
- [ ] Test: `https://your-backend.railway.app/api/health`
- [ ] Save backend URL

## Step 3: Frontend (Vercel)
- [ ] Create Vercel account
- [ ] Import GitHub repository
- [ ] Configure project:
  - [ ] Framework: Vite
  - [ ] Root Directory: `frontend`
  - [ ] Build Command: `npm run build`
  - [ ] Output Directory: `dist`
- [ ] Set environment variable: `VITE_API_URL`
- [ ] Deploy frontend
- [ ] Test frontend URL
- [ ] Verify connection to backend

## Step 4: Post-Deployment
- [ ] Sync tournament data via admin
- [ ] Import test entry
- [ ] Calculate scores
- [ ] Verify leaderboard works
- [ ] Test all admin features

## Step 5: Custom Domain (Optional)
- [ ] Add backend domain (Railway)
- [ ] Add frontend domain (Vercel)
- [ ] Update DNS records
- [ ] Update `VITE_API_URL` if needed
- [ ] Wait for SSL certificates

## Final Verification
- [ ] Backend health check passes
- [ ] Frontend loads correctly
- [ ] Tournament syncs successfully
- [ ] Entries can be imported
- [ ] Scores calculate correctly
- [ ] Leaderboard displays
- [ ] Admin dashboard works

---

**Notes:**
- Save all URLs and credentials securely
- Test each step before moving to next
- Check logs if anything fails
