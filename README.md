# Eldorado Masters Pool

A near real-time web application for managing an annual Masters golf tournament pool with custom scoring logic, SmartSheet imports, and live leaderboard updates.

## 🏌️ Overview

This application allows participants to:
- View real-time leaderboard with automatic updates
- See detailed scoring breakdowns
- Track bonus points and rebuys

Administrators can:
- Import participant entries from SmartSheet
- Import rebuys (missed cut / underperformer)
- Manually add GIR and Fairways bonus points
- Sync tournament data from Slash Golf API
- Calculate scores automatically

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL database (Supabase recommended)
- Slash Golf API key (RapidAPI)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env.template .env
   # Edit .env with your values
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Frontend Setup

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
   cp env.template .env
   # Edit .env with your API URL
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

## 📁 Project Structure

```
masters/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   └── main.py      # FastAPI application
│   ├── alembic/         # Database migrations
│   ├── tests/           # Test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── hooks/       # React Query hooks
│   │   ├── services/    # API client
│   │   └── types/       # TypeScript types
│   └── package.json
└── docs/                # Documentation
```

## 🎯 Features

### Scoring System

- **Daily Points**: Based on position after each round
  - Round 1: Leader (8), Top 5 (5), Top 10 (3), Top 25 (1)
  - Round 2: Leader (12), Top 5 (8), Top 10 (5), Top 25 (3), Made Cut (1)
  - Round 3-4: Leader (15), Top 5 (10), Top 10 (7), Top 25 (5), Made Cut (1)

- **Bonus Points**:
  - GIR Leader: 1 point (manual)
  - Fairways Leader: 1 point (manual)
  - Low Score of Day: 1 point
  - Eagle: 2 points
  - Double Eagle: 3 points
  - Hole-in-One: 3 points
  - All 6 Make Cut: 5 points (weekend only)

### Rebuy System

- **Missed Cut Rebuy**: Original player's points retained, rebuy player earns weekend points
- **Underperformer Rebuy**: Original player's points retained, weekend bonus forfeited

### Real-Time Updates

- Auto-refresh every 30 seconds
- Visual update indicators
- Smooth transitions
- Background job system for automatic score sync

## 📚 Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Development Plan](DEVELOPMENT_PLAN.md)
- [Setup Guide](SETUP_GUIDE.md)
- [SmartSheet Import Guide](docs/SMARTSHEET_FORMAT.md)
- [Backend Import Guide](backend/docs/IMPORT_GUIDE.md)
- [Manual Bonus Points Guide](backend/docs/MANUAL_BONUS_POINTS.md)

## 🔧 API Endpoints

### Public Endpoints

- `GET /api/tournament/current` - Get current tournament
- `GET /api/tournament/{id}` - Get tournament by ID
- `GET /api/scores/leaderboard?tournament_id={id}` - Get leaderboard
- `POST /api/scores/calculate?tournament_id={id}` - Calculate scores

### Admin Endpoints

- `POST /api/admin/import/entries` - Import entries from CSV
- `POST /api/admin/import/rebuys` - Import rebuys from CSV
- `POST /api/admin/bonus-points/add` - Add manual bonus point
- `GET /api/admin/players/search?name={name}` - Search players
- `POST /api/admin/jobs/start` - Start background job
- `POST /api/admin/jobs/stop` - Stop background job

See full API documentation at `/docs` when server is running.

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 📦 Deployment

### Backend (Railway/Render)

1. Connect your repository
2. Set environment variables
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel)

1. Connect your repository
2. Set build command: `cd frontend && npm install && npm run build`
3. Set output directory: `frontend/dist`
4. Set environment variable: `VITE_API_URL`

## 🔐 Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql://...
SLASH_GOLF_API_KEY=your_api_key
SLASH_GOLF_API_HOST=your_api_host
API_PREFIX=/api
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## 🛠️ Development

### Running in Development

1. **Start backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 📝 Usage Workflow

1. **Sync Tournament Data:**
   - Use `/api/tournament/sync` endpoint
   - Or use admin interface

2. **Import Entries:**
   - Export from SmartSheet as CSV
   - Use `/api/admin/import/entries` endpoint
   - Verify entries in leaderboard

3. **Import Rebuys (After Cut):**
   - Export rebuys from SmartSheet
   - Use `/api/admin/import/rebuys` endpoint

4. **Add Manual Bonuses:**
   - Use `/api/admin/bonus-points/add` for GIR/Fairways
   - Or use admin interface

5. **Calculate Scores:**
   - Scores auto-calculate on sync
   - Or manually trigger with `/api/scores/calculate`

6. **View Leaderboard:**
   - Visit frontend at configured URL
   - Leaderboard auto-updates every 30 seconds

## 🐛 Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` is correct
- Check Supabase project is active
- Ensure connection string uses correct format

### API Connection Issues

- Verify `SLASH_GOLF_API_KEY` is set
- Check API rate limits
- Verify network connectivity

### Import Errors

- Check CSV column names match exactly
- Verify player names match API data
- Review error messages in response

## 📄 License

Private project for Eldorado Masters Pool

## 👥 Contributors

Built for the 13th Annual Eldorado Masters Pool

## 🎉 Acknowledgments

- Slash Golf API for tournament data
- FastAPI for backend framework
- React + TypeScript for frontend
- Tailwind CSS for styling
