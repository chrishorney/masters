# Step-by-Step Setup Guide

This guide will walk you through setting up the Eldorado Masters Pool application from scratch, even if you've never done anything like this before.

## Prerequisites Check

Before we start, make sure you have:

1. **Git** installed
   - Check: Open terminal and type `git --version`
   - If not installed: Download from https://git-scm.com/

2. **Python 3.11+** installed
   - Check: Type `python3 --version` or `python --version`
   - If not installed: Download from https://www.python.org/downloads/

3. **Node.js 18+** installed
   - Check: Type `node --version`
   - If not installed: Download from https://nodejs.org/

4. **A code editor** (VS Code recommended)
   - Download from https://code.visualstudio.com/

5. **Slash Golf API Key** from RapidAPI
   - Sign up at https://rapidapi.com/
   - Subscribe to Slash Golf API
   - Get your API key

6. **Database** (choose one):
   - **Option A**: Supabase (free, recommended for beginners)
     - Sign up at https://supabase.com/
     - Create a new project
     - Get your database connection string
   - **Option B**: Local PostgreSQL
     - Install PostgreSQL from https://www.postgresql.org/download/

## Step 1: Initialize Git Repository

1. Open terminal/command prompt
2. Navigate to your project directory:
   ```bash
   cd "/Volumes/External HD/masters"
   ```

3. Initialize Git repository:
   ```bash
   git init
   ```

4. Create initial commit:
   ```bash
   git add .
   git commit -m "Initial commit: Project structure and documentation"
   ```

5. (Optional) Connect to GitHub:
   - Create a new repository on GitHub
   - Add remote:
     ```bash
     git remote add origin https://github.com/yourusername/eldorado-masters.git
     git branch -M main
     git push -u origin main
     ```

## Step 2: Set Up Backend

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create Python virtual environment:**
   ```bash
   python3 -m venv venv
   ```
   - On Windows: `python -m venv venv`

3. **Activate virtual environment:**
   ```bash
   # On Mac/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```
   - You should see `(venv)` in your terminal prompt

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   - Open `.env` file in your editor
   - Fill in your values:
     ```env
     DATABASE_URL=your_database_connection_string
     SLASH_GOLF_API_KEY=your_rapidapi_key
     JWT_SECRET_KEY=generate_a_random_string_here
     ```

6. **Generate JWT Secret Key:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   - Copy the output and paste it as `JWT_SECRET_KEY` in `.env`

## Step 3: Set Up Database

### If using Supabase:

1. Go to your Supabase project dashboard
2. Click on "Settings" → "Database"
3. Find "Connection string" under "Connection pooling"
4. Copy the connection string (it looks like: `postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres`)
5. Replace `[YOUR-PASSWORD]` with your actual database password
6. Paste this into your `.env` file as `DATABASE_URL`

### If using local PostgreSQL:

1. Create database:
   ```bash
   createdb eldorado_masters
   ```
   - Or use pgAdmin GUI

2. Update `.env`:
   ```env
   DATABASE_URL=postgresql://username:password@localhost/eldorado_masters
   ```

3. **Run database migrations:**
   ```bash
   cd backend
   source venv/bin/activate  # Make sure venv is activated
   alembic upgrade head
   ```

## Step 4: Test Backend

1. **Start the backend server:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Open in browser:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

3. **Test health endpoint:**
   - Visit: http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

4. **Stop server:** Press `Ctrl+C` in terminal

## Step 5: Set Up Frontend

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env`:**
   ```env
   VITE_API_URL=http://localhost:8000
   ```

5. **Start development server:**
   ```bash
   npm run dev
   ```

6. **Open in browser:**
   - Frontend: http://localhost:5173

7. **Stop server:** Press `Ctrl+C` in terminal

## Step 6: Run Tests

### Backend Tests:

```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests:

```bash
cd frontend
npm test
```

## Step 7: Development Workflow

### Daily Development:

1. **Start Backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Start Frontend (in new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Make changes** to code
4. **Test changes** in browser
5. **Run tests** before committing

### Git Workflow:

1. **Check status:**
   ```bash
   git status
   ```

2. **Add changes:**
   ```bash
   git add .
   ```

3. **Commit:**
   ```bash
   git commit -m "Description of changes"
   ```

4. **Push (if connected to GitHub):**
   ```bash
   git push origin main
   ```

## Step 8: Common Issues & Solutions

### Issue: "Module not found"
**Solution:** Make sure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Database connection error"
**Solution:** 
- Check `.env` file has correct `DATABASE_URL`
- Make sure database is running (if local)
- Check Supabase connection string is correct

### Issue: "Port already in use"
**Solution:** 
- Change port in backend: `uvicorn app.main:app --reload --port 8001`
- Or kill process using port: `lsof -ti:8000 | xargs kill`

### Issue: "API key not working"
**Solution:**
- Verify API key in RapidAPI dashboard
- Check `.env` file has correct key
- Restart backend server after changing `.env`

## Step 9: Next Steps

Once setup is complete:

1. **Read the documentation:**
   - [ARCHITECTURE.md](./ARCHITECTURE.md) - Understand the system
   - [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) - See development phases

2. **Start Phase 1 development:**
   - Follow the tasks in DEVELOPMENT_PLAN.md
   - Run tests after each feature
   - Commit frequently

3. **Ask questions:**
   - Review test scripts for examples
   - Check API documentation at `/docs`
   - Review code comments

## Step 10: Deployment Preparation

When ready to deploy:

1. **Backend (Railway):**
   - Sign up at https://railway.app/
   - Connect GitHub repository
   - Add environment variables
   - Deploy

2. **Frontend (Vercel):**
   - Sign up at https://vercel.com/
   - Connect GitHub repository
   - Add environment variables
   - Deploy

3. **Database:**
   - Use Supabase (already cloud-hosted)
   - Or set up Railway PostgreSQL

## Tips for Beginners

1. **Take it one step at a time** - Don't try to understand everything at once
2. **Use the test scripts** - They show how things should work
3. **Read error messages** - They usually tell you what's wrong
4. **Commit often** - Small commits are easier to understand
5. **Ask for help** - Review documentation and test examples

## Getting Help

- Check test scripts in `backend/tests/` for examples
- Review API documentation at `http://localhost:8000/docs`
- Read code comments
- Check error logs in terminal

---

**You're all set! Start with Phase 1 in DEVELOPMENT_PLAN.md**
