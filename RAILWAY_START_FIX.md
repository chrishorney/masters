# Railway Start Command Fix

## Problem
Railway detected Python but can't find the start command.

## Solution Options

### Option 1: Set Start Command in Railway Dashboard (Recommended)

1. Go to your Railway service
2. Click on **Settings** tab
3. Scroll to **"Deploy"** section
4. Find **"Start Command"** field
5. Enter exactly:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
6. Click **"Save"**
7. Railway will automatically redeploy

### Option 2: Push Latest Changes

I've created multiple configuration files that should help Railway auto-detect:

- ✅ `railway.json` - Railway-specific config
- ✅ `Procfile` - Standard start command
- ✅ `nixpacks.toml` - Nixpacks build config
- ✅ `start.sh` - Executable start script

**Push to GitHub and Railway will auto-redeploy:**

```bash
git push origin main
```

### Option 3: Use Railway CLI

If you have Railway CLI installed:

```bash
railway variables set START_COMMAND="uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

## What I've Created

### Files Added:
1. **`backend/railway.json`** - Railway deployment config
2. **`backend/start.sh`** - Executable start script (runs migrations + starts server)
3. **Updated `backend/Procfile`** - Now uses start.sh
4. **Updated `backend/nixpacks.toml`** - Explicit start command

### Start Command Details:
- **Module**: `app.main:app` (FastAPI app is at `app/main.py`)
- **Host**: `0.0.0.0` (listens on all interfaces)
- **Port**: `$PORT` (Railway sets this automatically)

## Verification

After setting the start command, check the logs:

1. Railway Dashboard → Your Service → **Logs**
2. You should see:
   ```
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:PORT
   ```

3. Test the health endpoint:
   ```
   https://your-app.railway.app/health
   ```

## Troubleshooting

### Still Not Starting?
1. **Check logs** - Railway Dashboard → Logs tab
2. **Verify Root Directory** - Should be set to `backend`
3. **Check environment variables** - Make sure `DATABASE_URL` is set
4. **Try manual start command** - Use Option 1 above

### "Module not found" error?
- Make sure Root Directory is `backend`
- Railway needs to be in `backend/` to find the `app/` module

### "Port already in use"?
- Make sure you're using `$PORT` not a hardcoded port
- Railway sets `$PORT` automatically

### Database connection errors?
- Check `DATABASE_URL` environment variable
- Make sure it's the full connection string from Supabase
- Format: `postgresql://user:password@host:port/dbname`

## Quick Checklist

- [ ] Root Directory set to `backend` ✅
- [ ] Start Command set: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Environment variables added (DATABASE_URL, etc.)
- [ ] Latest code pushed to GitHub
- [ ] Build succeeds
- [ ] Server starts (check logs)
- [ ] Health endpoint works: `/health`

---

**Next Step:** Set the start command in Railway Dashboard (Option 1) - this is the fastest fix!
