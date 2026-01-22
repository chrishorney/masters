# Where to Put Your Credentials

This guide shows you exactly where to put each piece of information.

## Supabase Connection String

You'll need this in **two places**:

### 1. Local Testing (backend/.env file)

**Location**: `/Volumes/External HD/masters/backend/.env`

**Steps:**
1. Copy the connection string from Supabase
2. Open or create `backend/.env` file
3. Add this line:

```env
DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[YOUR-PASSWORD]@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

**Example:**
```env
DATABASE_URL=postgresql://postgres.abcdefghijklmnop:MyPassword123!@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

**Important**: 
- Replace `[PROJECT_REF]` with your actual project reference (from Supabase)
- Replace `[YOUR-PASSWORD]` with your actual database password
- If your password has special characters, URL-encode them:
  - `!` becomes `%21`
  - `@` becomes `%40`
  - `#` becomes `%23`
  - etc.

**How to get it:**
1. Go to Supabase → Your Project
2. Click **Settings** (gear icon) → **Database**
3. Scroll to **Connection string**
4. Click **Connection pooling** tab
5. Copy the string (it looks like the example above)

### 2. Production Backend (Railway Environment Variables)

**Location**: Railway Dashboard → Your Service → Variables Tab

**Steps:**
1. Go to https://railway.app
2. Open your project
3. Click on your backend service
4. Go to **Variables** tab
5. Click **"New Variable"**
6. Name: `DATABASE_URL`
7. Value: Paste your connection string (same as above)
8. Click **"Add"**

**Same connection string** - just copy it from your local `.env` file!

---

## Slash Golf API Key

### 1. Local Testing (backend/.env file)

**Location**: `/Volumes/External HD/masters/backend/.env`

Add these lines:

```env
SLASH_GOLF_API_KEY=your_rapidapi_key_here
SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com
```

**How to get API key:**
1. Go to https://rapidapi.com
2. Sign up or log in
3. Search for "Slash Golf" or the API you're using
4. Subscribe (free tier usually available)
5. Go to your dashboard
6. Copy your API key

### 2. Production Backend (Railway Environment Variables)

**Location**: Railway Dashboard → Your Service → Variables Tab

Add two variables:
- **Name**: `SLASH_GOLF_API_KEY`, **Value**: `your_rapidapi_key_here`
- **Name**: `SLASH_GOLF_API_HOST`, **Value**: `live-golf-data.p.rapidapi.com`

---

## Backend URL (for Frontend)

### Production Frontend (Vercel Environment Variables)

**Location**: Vercel Dashboard → Your Project → Settings → Environment Variables

**Steps:**
1. Go to https://vercel.com
2. Open your project
3. Go to **Settings** → **Environment Variables**
4. Click **"Add New"**
5. Name: `VITE_API_URL`
6. Value: `https://your-backend-name.railway.app` (your actual Railway URL)
7. Click **"Save"**

**Note**: You'll get the Railway URL after deploying the backend (Step 2.5 in PRODUCTION_DEPLOY.md)

---

## Complete Example: backend/.env file

Here's what your complete `backend/.env` file should look like:

```env
# Database (from Supabase)
DATABASE_URL=postgresql://postgres.abcdefghijklmnop:MyPassword%21@aws-1-us-east-2.pooler.supabase.com:5432/postgres

# Slash Golf API (from RapidAPI)
SLASH_GOLF_API_KEY=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com

# Application Settings
API_PREFIX=/api
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Important Notes:**
- The `.env` file is in `.gitignore` - it won't be committed to git
- Never share your `.env` file or commit it
- Use the same values in Railway (except `ENVIRONMENT` can stay `production`)

---

## Quick Reference: Where Each Goes

| Credential | Local File | Production Service |
|------------|------------|-------------------|
| Database URL | `backend/.env` | Railway Variables |
| API Key | `backend/.env` | Railway Variables |
| API Host | `backend/.env` | Railway Variables |
| Backend URL | N/A | Vercel Variables (as `VITE_API_URL`) |

---

## Step-by-Step: Setting Up Local .env

1. **Navigate to backend folder:**
   ```bash
   cd "/Volumes/External HD/masters/backend"
   ```

2. **Check if .env exists:**
   ```bash
   ls -la .env
   ```

3. **Create or edit .env:**
   ```bash
   # If it doesn't exist, create it:
   cp env.template .env
   
   # Then edit it with your values
   ```

4. **Add your values** (see example above)

5. **Test the connection:**
   ```bash
   source venv/bin/activate
   export DATABASE_URL="your_connection_string"
   alembic upgrade head
   ```

---

## Troubleshooting

**Problem**: Can't find `.env` file
- It might be hidden (starts with `.`)
- Use `ls -la` to see hidden files
- Create it if it doesn't exist: `touch .env`

**Problem**: Connection string not working
- Check password is URL-encoded
- Verify project reference is correct
- Make sure you're using "Connection pooling" format
- Test connection string format

**Problem**: Don't know where to find values
- Supabase: Settings → Database → Connection string
- RapidAPI: Dashboard → Your Apps → API Key
- Railway URL: After deployment, shown in dashboard
