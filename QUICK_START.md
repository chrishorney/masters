# Quick Start Guide

This is a condensed version of the setup process. For detailed instructions, see [SETUP_GUIDE.md](./SETUP_GUIDE.md).

## Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Database (Supabase recommended)
- Slash Golf API key (RapidAPI)

## 5-Minute Setup

### 1. Initialize Git
```bash
cd "/Volumes/External HD/masters"
git init
git add .
git commit -m "Initial commit"
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```env
DATABASE_URL=your_database_url
SLASH_GOLF_API_KEY=your_api_key
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 3. Database Setup
```bash
# If using Supabase, get connection string from dashboard
# Then run migrations:
alembic upgrade head
```

### 4. Frontend Setup
```bash
cd frontend
npm install
```

Create `.env` file:
```env
VITE_API_URL=http://localhost:8000
```

### 5. Run Everything
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Visit:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Next Steps

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand the system
2. Follow [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) Phase 1
3. Run tests: `pytest` (backend) and `npm test` (frontend)

## Common Commands

```bash
# Backend
pytest                    # Run tests
alembic revision --autogenerate -m "message"  # Create migration
alembic upgrade head       # Apply migrations

# Frontend
npm run dev               # Development server
npm run build             # Production build
npm test                  # Run tests
```

## Getting Help

- Check [SETUP_GUIDE.md](./SETUP_GUIDE.md) for detailed setup
- Review test files for examples
- Check API docs at `/docs` endpoint
