# Deployment Guide

This guide walks you through deploying the Eldorado Masters Pool application to production.

## Overview

The application consists of:
- **Backend**: FastAPI application (deploy to Railway, Render, or similar)
- **Frontend**: React application (deploy to Vercel, Netlify, or similar)
- **Database**: PostgreSQL (Supabase recommended)

## Prerequisites

- GitHub repository (or GitLab/Bitbucket)
- Supabase account (for database)
- Railway/Render account (for backend)
- Vercel account (for frontend)
- Domain name (optional but recommended)

## Step 1: Database Setup (Supabase)

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Note your project credentials

2. **Get Connection String**
   - Go to Project Settings → Database
   - Copy the connection string
   - Use the "Connection pooling" format for production:
     ```
     postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-us-east-2.pooler.supabase.com:5432/postgres
     ```

3. **Run Migrations**
   ```bash
   cd backend
   source venv/bin/activate
   export DATABASE_URL="your_connection_string"
   alembic upgrade head
   ```

## Step 2: Backend Deployment (Railway)

### Option A: Railway

1. **Connect Repository**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure Service**
   - Railway will auto-detect Python
   - Set root directory: `backend`
   - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**
   ```
   DATABASE_URL=your_supabase_connection_string
   SLASH_GOLF_API_KEY=your_api_key
   SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com
   API_PREFIX=/api
   ENVIRONMENT=production
   ```

4. **Deploy**
   - Railway will automatically deploy on push to main
   - Get your backend URL (e.g., `https://your-app.railway.app`)

### Option B: Render

1. **Create Web Service**
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure**
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Root Directory: `backend`

3. **Set Environment Variables** (same as Railway)

4. **Deploy**
   - Render will build and deploy automatically

## Step 3: Frontend Deployment (Vercel)

1. **Connect Repository**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository

2. **Configure Project**
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Set Environment Variables**
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   ```

4. **Deploy**
   - Vercel will automatically deploy
   - Get your frontend URL (e.g., `https://your-app.vercel.app`)

## Step 4: Domain Configuration

### Backend Domain (Optional)

1. **Add Custom Domain in Railway/Render**
   - Go to your service settings
   - Add custom domain (e.g., `api.yourdomain.com`)
   - Update DNS records as instructed

2. **Update Frontend Environment Variable**
   - Update `VITE_API_URL` to use your custom domain

### Frontend Domain

1. **Add Custom Domain in Vercel**
   - Go to project settings → Domains
   - Add your domain (e.g., `yourdomain.com`)
   - Update DNS records as instructed

## Step 5: Post-Deployment Setup

1. **Verify Database Connection**
   ```bash
   # Test connection
   cd backend
   source venv/bin/activate
   python test_db_connection.py
   ```

2. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

3. **Test API**
   - Visit: `https://your-backend-url/docs`
   - Test health endpoint: `https://your-backend-url/api/health`

4. **Test Frontend**
   - Visit your frontend URL
   - Verify it connects to backend

5. **Initial Tournament Setup**
   - Use admin interface to sync tournament
   - Import entries from SmartSheet
   - Test score calculation

## Step 6: Monitoring & Maintenance

### Health Checks

The backend includes a health check endpoint:
- `GET /api/health` - Returns API status

### Logs

- **Railway**: View logs in dashboard
- **Render**: View logs in dashboard
- **Vercel**: View logs in dashboard

### Database Backups

Supabase provides automatic backups. You can also:
- Export data manually from Supabase dashboard
- Set up scheduled backups if needed

## Environment Variables Reference

### Backend

```env
# Database
DATABASE_URL=postgresql://...

# Slash Golf API
SLASH_GOLF_API_KEY=your_rapidapi_key
SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com

# Application
API_PREFIX=/api
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Frontend

```env
VITE_API_URL=https://your-backend-url.railway.app
```

## Troubleshooting

### Backend Won't Start

1. Check environment variables are set
2. Verify database connection string
3. Check logs for errors
4. Ensure port is set to `$PORT` (Railway/Render requirement)

### Frontend Can't Connect to Backend

1. Verify `VITE_API_URL` is correct
2. Check CORS settings (should be configured in backend)
3. Verify backend is running and accessible
4. Check browser console for errors

### Database Connection Issues

1. Verify connection string format
2. Check Supabase project is active
3. Verify IP allowlist (if configured)
4. Test connection with `test_db_connection.py`

### Import Errors

1. Check CSV format matches requirements
2. Verify player names match API data
3. Check error messages in admin UI
4. Review import logs

## Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Keep secure, rotate if compromised
3. **Database**: Use connection pooling URL
4. **CORS**: Configure allowed origins in production
5. **Rate Limiting**: Consider adding rate limiting for API

## Scaling Considerations

- **Database**: Supabase handles scaling automatically
- **Backend**: Railway/Render auto-scales based on traffic
- **Frontend**: Vercel CDN handles scaling automatically
- **API Rate Limits**: Monitor Slash Golf API usage

## Cost Estimation

- **Supabase**: Free tier (500MB database, 2GB bandwidth)
- **Railway**: $5/month starter plan
- **Render**: Free tier available (with limitations)
- **Vercel**: Free tier (100GB bandwidth)
- **Domain**: ~$10-15/year

## Rollback Plan

If deployment fails:

1. **Backend**: Revert to previous deployment in Railway/Render
2. **Frontend**: Revert to previous deployment in Vercel
3. **Database**: Restore from Supabase backup if needed

## Next Steps After Deployment

1. Test all functionality with real data
2. Set up monitoring/alerting
3. Configure custom domain
4. Set up automated backups
5. Document production URLs and credentials
6. Train admin users on the system

## Support

For deployment issues:
1. Check service provider documentation
2. Review application logs
3. Test locally first
4. Verify environment variables
