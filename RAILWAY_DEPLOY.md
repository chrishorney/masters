# Railway Deployment Guide

## Problem: Railway Can't Detect Build Configuration

If you see this error:
```
✖ Railpack could not determine how to build the app.
```

This means Railway is looking at the root directory and seeing both `backend/` and `frontend/` folders, so it doesn't know which one to build.

## Solution: Configure Railway to Use Backend Directory

### Option 1: Set Root Directory in Railway (Recommended)

1. **In Railway Dashboard:**
   - Go to your service settings
   - Find **"Root Directory"** or **"Source"** setting
   - Set it to: `backend`
   - Save changes
   - Redeploy

2. **Railway will now:**
   - Look in `backend/` directory
   - Detect `requirements.txt` (Python project)
   - Use `Procfile` or `nixpacks.toml` for build/start commands

### Option 2: Create Separate Services

Create **two separate services** in Railway:

1. **Backend Service:**
   - Connect to GitHub repository
   - Set **Root Directory**: `backend`
   - Railway will auto-detect Python

2. **Frontend Service** (optional, or use Vercel):
   - Connect to GitHub repository  
   - Set **Root Directory**: `frontend`
   - Railway will auto-detect Node.js

## Files Created for Railway

I've created these files in `backend/`:

- ✅ `Procfile` - Tells Railway how to start the app
- ✅ `nixpacks.toml` - Advanced build configuration
- ✅ `runtime.txt` - Specifies Python version

## Railway Configuration Steps

### Step 1: Create New Service

1. Go to Railway dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will create a service

### Step 2: Configure Root Directory

1. Click on your service
2. Go to **Settings** tab
3. Find **"Root Directory"** setting
4. Enter: `backend`
5. Click **"Save"**

### Step 3: Set Environment Variables

In Railway service settings, add these environment variables:

```
DATABASE_URL=postgresql://user:password@host:port/dbname
SLASH_GOLF_API_KEY=your_api_key_here
CORS_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:5173
LOG_LEVEL=INFO
```

**Important:** Get `DATABASE_URL` from your Supabase project settings.

### Step 4: Deploy

1. Railway will automatically detect the changes
2. Or click **"Deploy"** button
3. Watch the build logs

### Step 5: Verify Deployment

1. Railway will give you a URL like: `https://your-app.railway.app`
2. Test health endpoint: `https://your-app.railway.app/health`
3. Test API docs: `https://your-app.railway.app/docs`

## Build Process

Railway will:
1. ✅ Detect Python from `requirements.txt`
2. ✅ Install dependencies: `pip install -r requirements.txt`
3. ✅ Run migrations: `alembic upgrade head` (from `nixpacks.toml`)
4. ✅ Start server: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Troubleshooting

### Problem: "No module named 'app'"
- **Fix:** Make sure Root Directory is set to `backend`
- Railway needs to be in the `backend/` directory to find the `app/` module

### Problem: "Database connection failed"
- **Fix:** Check `DATABASE_URL` environment variable
- Make sure it's the full connection string from Supabase
- Format: `postgresql://user:password@host:port/dbname`

### Problem: "Alembic migration failed"
- **Fix:** Check database connection first
- Make sure `DATABASE_URL` is correct
- You can skip migrations in build if needed (remove from `nixpacks.toml`)

### Problem: "Port already in use"
- **Fix:** Railway sets `$PORT` automatically
- Make sure `Procfile` uses `$PORT` not a hardcoded port

### Problem: Build succeeds but app crashes
- **Check logs:** Railway dashboard → Service → Logs
- **Common issues:**
  - Missing environment variables
  - Database connection string wrong
  - CORS origins not set correctly

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SLASH_GOLF_API_KEY` | RapidAPI key for Slash Golf API | `your-api-key` |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) | `https://app.vercel.app,http://localhost:5173` |
| `LOG_LEVEL` | Logging level | `INFO`, `DEBUG`, `WARNING` |
| `PORT` | Server port (auto-set by Railway) | `8000` |

## Next Steps After Backend Deployment

1. ✅ Get your Railway backend URL
2. ✅ Update frontend `.env` with Railway URL
3. ✅ Deploy frontend to Vercel
4. ✅ Update Railway `CORS_ORIGINS` with Vercel URL
5. ✅ Test full stack

## Quick Checklist

- [ ] Railway service created
- [ ] Root Directory set to `backend`
- [ ] Environment variables added
- [ ] Build succeeds
- [ ] Health endpoint works: `/health`
- [ ] API docs accessible: `/docs`
- [ ] Database migrations ran successfully

---

## Alternative: Use Railway CLI

If you prefer command line:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Set root directory
railway variables set RAILWAY_SERVICE_ROOT=backend

# Deploy
railway up
```
