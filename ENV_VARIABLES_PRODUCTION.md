# Production Environment Variables Reference

## Backend Environment Variables (Railway/Render)

Copy these into your backend hosting service:

```env
# Database (from Supabase)
DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-us-east-2.pooler.supabase.com:5432/postgres

# Slash Golf API (from RapidAPI)
SLASH_GOLF_API_KEY=your_rapidapi_key_here
SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com

# JWT Authentication
JWT_SECRET_KEY=your_random_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Application
API_PREFIX=/api
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### How to Get Each Value:

**DATABASE_URL:**
1. Go to Supabase → Your Project → Settings → Database
2. Scroll to "Connection string"
3. Select "Connection pooling" tab
4. Copy the string
5. Replace `[YOUR-PASSWORD]` with your actual password
6. URL-encode special characters (e.g., `!` → `%21`)

**SLASH_GOLF_API_KEY:**
1. Go to https://rapidapi.com
2. Sign up or log in
3. Subscribe to "Slash Golf API" (or whatever it's called)
4. Copy your API key from the dashboard

**SLASH_GOLF_API_HOST:**
- Use: `live-golf-data.p.rapidapi.com`
- (This is the standard host for the API)

**JWT_SECRET_KEY:**
- Generate a random secret string (at least 32 characters)
- You can use: `openssl rand -hex 32` or any long random string
- This is used to sign JWT tokens for authentication
- Keep this secret and never commit it to Git

## Frontend Environment Variables (Vercel)

```env
VITE_API_URL=https://your-backend-url.railway.app
```

**VITE_API_URL:**
- Use your Railway backend URL (from Step 2)
- Format: `https://your-app-name.railway.app`
- No trailing slash

## Important Notes

1. **Never commit `.env` files** - they're in `.gitignore`
2. **URL-encode passwords** - Special characters need encoding
3. **Test each variable** - Verify they work before deploying
4. **Keep backups** - Save all credentials securely

## Testing Environment Variables

**Backend:**
```bash
curl https://your-backend.railway.app/api/health
```

**Frontend:**
- Visit your Vercel URL
- Check browser console for API connection errors
- Verify leaderboard loads data
