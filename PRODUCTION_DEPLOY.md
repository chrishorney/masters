# Production Deployment - Step by Step

This guide will walk you through deploying the Eldorado Masters Pool to production.

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] GitHub repository (code pushed and backed up)
- [ ] Supabase account (free tier works)
- [ ] Railway account (or Render) for backend
- [ ] Vercel account (free tier works) for frontend
- [ ] Domain name (optional but recommended)
- [ ] Slash Golf API key (RapidAPI)

## Quick Reference - Production URLs

**Backend (Railway):**
- URL: `https://masters-production.up.railway.app`
- Health Check: `https://masters-production.up.railway.app/api/health`
- API Docs: `https://masters-production.up.railway.app/docs`

**Frontend (Vercel):**
- URL: `https://masters-livid.vercel.app`
- Admin Page: `https://masters-livid.vercel.app/admin`

**Database (Supabase):**
- Connection: (See Step 1.2 for connection string)

## Step 1: Database Setup (Supabase) - 5 minutes

### 1.1 Create Supabase Project
1. Go to https://supabase.com
2. Sign up or log in
3. Click "New Project"
4. Fill in:
   - **Name**: `eldorado-masters-pool` (or your choice)
   - **Database Password**: Create a strong password (save it!)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Free tier is fine
5. Click "Create new project"
6. Wait 2-3 minutes for project to initialize

### 1.2 Get Connection String
1. In your Supabase project, go to **Settings** → **Database**
2. Scroll down to **Connection string**
3. Select **Connection pooling** tab
4. Copy the connection string (looks like):
   ```
   postgresql://postgres.[PROJECT_REF]:[YOUR-PASSWORD]@aws-1-us-east-2.pooler.supabase.com:5432/postgres
   ```
5. **Important**: Replace `[YOUR-PASSWORD]` with your actual database password
6. URL-encode special characters in password (e.g., `!` becomes `%21`)

### 1.3 Run Database Migrations
```bash
cd backend
source venv/bin/activate
export DATABASE_URL="your_connection_string_here"
alembic upgrade head
```

You should see:
```
INFO  [alembic.runtime.migration] Running upgrade  -> fd7c075d609b, Initial database schema
```

✅ **Step 1 Complete** - Database is ready!

---

## Step 2: Backend Deployment (Railway) - 10 minutes

### 2.1 Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub (recommended)
3. Verify your email

### 2.2 Create New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Authorize Railway to access your GitHub
4. Select your `masters` repository
5. Railway will detect it's a Python project

### 2.3 Configure Service
1. Railway will create a service automatically
2. Click on the service to configure it
3. Go to **Settings** tab
4. Set:
   - **Root Directory**: `backend`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2.4 Set Environment Variables
1. Go to **Variables** tab
2. Click **"New Variable"** and add each:

```
DATABASE_URL=your_supabase_connection_string
SLASH_GOLF_API_KEY=your_rapidapi_key
SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com
JWT_SECRET_KEY=your_random_secret_key
CORS_ORIGINS=https://masters-livid.vercel.app,http://localhost:5173,http://localhost:3000
API_PREFIX=/api
ENVIRONMENT=production
LOG_LEVEL=INFO
```

3. **Important**: 
   - Use the connection string from Step 1.2
   - Get your RapidAPI key from https://rapidapi.com
   - Make sure `DATABASE_URL` is the connection pooling URL
   - Generate `JWT_SECRET_KEY` with: `openssl rand -hex 32`
   - Update `CORS_ORIGINS` with your actual Vercel frontend URL after Step 3
   - **Current production URL**: `https://masters-livid.vercel.app`

### 2.5 Deploy
1. Railway will automatically deploy when you push to main
2. Or click **"Deploy"** button
3. Wait for deployment (2-3 minutes)
4. Once deployed, Railway will give you a URL like: `https://your-app.railway.app`

### 2.6 Test Backend
1. Visit: `https://your-app.railway.app/api/health`
2. Should return: `{"status": "healthy", ...}`
3. Visit: `https://your-app.railway.app/docs` for API documentation

✅ **Step 2 Complete** - Backend is live!

**Backend URL (Production):**
```
https://masters-production.up.railway.app
```

**Save your backend URL** - you'll need it for the frontend!

---

## Step 3: Frontend Deployment (Vercel) - 5 minutes

### 3.1 Create Vercel Account
1. Go to https://vercel.com
2. Sign up with GitHub (recommended)
3. Verify your email

### 3.2 Import Project
1. Click **"Add New Project"**
2. Import your GitHub repository
3. Select your `masters` repository

### 3.3 Configure Project
1. **Framework Preset**: Vite
2. **Root Directory**: `frontend`
3. **Build Command**: `npm run build`
4. **Output Directory**: `dist`
5. **Install Command**: `npm install`

### 3.4 Set Environment Variables
1. In project settings, go to **Environment Variables**
2. Add:
   ```
   VITE_API_URL=https://masters-production.up.railway.app
   ```
   (This is your Railway backend URL from Step 2.5)
3. **Important**: After adding, Vercel will automatically redeploy. Wait for the new deployment to complete.

### 3.5 Deploy
1. Click **"Deploy"**
2. Wait 1-2 minutes
3. Vercel will give you a URL like: `https://your-app.vercel.app`

**Frontend URL (Production):**
```
https://masters-livid.vercel.app
```

### 3.6 Test Frontend
1. Visit your Vercel URL: `https://masters-livid.vercel.app`
2. Should see the home page
3. Check leaderboard page
4. Verify it connects to backend
5. Test admin page: `https://masters-livid.vercel.app/admin`

✅ **Step 3 Complete** - Frontend is live!

### 3.7 Troubleshooting: Frontend Not Loading Data

If your frontend loads but shows no data, check:

1. **Vercel Environment Variable**:
   - Go to Vercel → Your Project → Settings → Environment Variables
   - Verify `VITE_API_URL` is set to: `https://masters-production.up.railway.app`
   - If missing or wrong, add/update it and redeploy

2. **Backend CORS Configuration**:
   - Go to Railway → Your Service → Variables
   - Check `CORS_ORIGINS` includes your Vercel URL:
     ```
     https://masters-livid.vercel.app,http://localhost:5173,http://localhost:3000
     ```
   - If missing, add it and Railway will restart

3. **Browser Console**:
   - Open browser DevTools (F12) → Console tab
   - Look for CORS errors or API connection errors
   - Check Network tab to see if API calls are failing

4. **Test API Directly**:
   ```bash
   curl https://masters-production.up.railway.app/api/health
   ```
   Should return: `{"status":"healthy",...}`

---

## Step 4: Custom Domain (Optional) - 10 minutes

### 4.1 Backend Domain
1. In Railway, go to your service → **Settings** → **Domains**
2. Click **"Generate Domain"** or **"Add Custom Domain"**
3. If custom: Add your domain (e.g., `api.yourdomain.com`)
4. Update DNS records as instructed
5. Update frontend `VITE_API_URL` to use new domain

### 4.2 Frontend Domain
1. In Vercel, go to project → **Settings** → **Domains**
2. Add your domain (e.g., `yourdomain.com`)
3. Update DNS records as instructed
4. Wait for SSL certificate (automatic, ~5 minutes)

✅ **Step 4 Complete** - Custom domain configured!

---

## Step 5: Post-Deployment Setup - 5 minutes

### 5.1 Verify Database Connection
```bash
# Test from local machine
curl https://your-backend-url.railway.app/api/health
```

### 5.2 Sync Tournament Data
1. Visit your frontend admin page: `https://your-app.vercel.app/admin`
2. Go to **Tournament Management** tab
3. Click **"Sync Tournament"**
4. Enter:
   - Org ID: `1` (PGA Tour)
   - Tournament ID: `002` (or current tournament)
   - Year: `2026` (current year)
5. Click **"Sync"**
6. Wait for sync to complete

### 5.3 Import Test Entry
1. Create a test CSV with one entry
2. Go to **Import** tab
3. Upload entries CSV
4. Verify entry appears in leaderboard

### 5.4 Test Score Calculation
1. In **Tournament Management** tab
2. Click **"Calculate Scores"**
3. Verify scores appear in leaderboard

✅ **Step 5 Complete** - System is operational!

---

## Step 6: Final Verification

### Checklist
- [ ] Backend health check returns healthy
- [ ] Frontend loads without errors
- [ ] Tournament syncs successfully
- [ ] Entries can be imported
- [ ] Scores calculate correctly
- [ ] Leaderboard displays properly
- [ ] Admin dashboard works
- [ ] Custom domain works (if configured)

---

## Troubleshooting

### Backend Issues
**Problem**: Backend won't start
- Check environment variables are set correctly
- Verify `DATABASE_URL` format
- Check Railway logs for errors

**Problem**: Database connection fails
- Verify connection string format
- Check Supabase project is active
- Ensure password is URL-encoded

### Frontend Issues
**Problem**: Can't connect to backend
- Verify `VITE_API_URL` is correct
- Check CORS settings (should be automatic)
- Test backend URL directly in browser

**Problem**: Build fails
- Check Node.js version (should be 18+)
- Verify all dependencies in package.json
- Check build logs in Vercel

### Database Issues
**Problem**: Migrations fail
- Verify connection string
- Check Supabase project status
- Try running migrations locally first

---

## Support Resources

- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Project README**: See `README.md`

---

## Next Steps After Deployment

1. **Import Real Entries**: Use SmartSheet export to import all entries
2. **Monitor**: Watch logs during first tournament
3. **Test**: Verify all features work in production
4. **Share**: Send leaderboard URL to participants
5. **Iterate**: Make improvements based on feedback

---

## Cost Estimate

- **Supabase**: Free tier (500MB database, 2GB bandwidth)
- **Railway**: $5/month starter plan (or free trial)
- **Vercel**: Free tier (100GB bandwidth)
- **Domain**: ~$10-15/year (optional)

**Total**: ~$5-15/month (or free if using free tiers)

---

## 🎉 You're Live!

Your application is now in production! Share the leaderboard URL with participants and start tracking the tournament!
