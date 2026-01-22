# Quick Setup: Local .env File

## Step 1: Create the .env file

```bash
cd "/Volumes/External HD/masters/backend"
cp env.template .env
```

## Step 2: Edit the .env file

Open `backend/.env` in your text editor and fill in:

### From Supabase:
```env
DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

**To get this:**
1. Supabase Dashboard → Your Project
2. Settings → Database
3. Scroll to "Connection string"
4. Click "Connection pooling" tab
5. Copy the string
6. Replace `[YOUR-PASSWORD]` with your actual password
7. URL-encode special characters (e.g., `!` → `%21`)

### From RapidAPI:
```env
SLASH_GOLF_API_KEY=your_key_here
SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com
```

## Step 3: Test it works

```bash
cd "/Volumes/External HD/masters/backend"
source venv/bin/activate
export DATABASE_URL="$(grep DATABASE_URL .env | cut -d '=' -f2-)"
alembic upgrade head
```

If this works, you're ready to deploy!
