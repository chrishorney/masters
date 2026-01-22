# Eldorado Masters Pool Application

A near real-time web application for managing and displaying the annual Eldorado Masters Golf Tournament pool with complex scoring rules, bonus points, and re-buy functionality.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Scoring Rules](#scoring-rules)
- [Contributing](#contributing)

## 🎯 Overview

This application manages a Masters Golf Tournament pool where participants:
- Pick 6 golfers from the Masters field
- Earn points based on daily performance and positions
- Can re-buy players who miss the cut or underperform
- Compete for a share of the prize pool

The app provides:
- Real-time score updates during the tournament
- Live leaderboard with detailed scoring breakdowns
- Admin interface for managing entries and re-buys
- Historical data tracking

## ✨ Features

### For Participants
- **Live Leaderboard**: See real-time standings with point breakdowns
- **Entry Details**: View your selected players and their performance
- **Daily Scoring**: See how points are earned each day
- **Bonus Points**: Track all bonus point opportunities
- **Mobile Responsive**: Access from any device

### For Administrators
- **SmartSheet Import**: Import entries and re-buys from SmartSheet exports
- **Manual Score Refresh**: Trigger score updates on demand
- **Entry Management**: View and manage all entries
- **Tournament Configuration**: Set up and configure tournaments

## 🛠 Technology Stack

### Backend
- **Python 3.11+** with **FastAPI** - Modern, fast web framework
- **PostgreSQL** - Relational database (via Supabase)
- **SQLAlchemy** - ORM for database operations
- **httpx** - Async HTTP client for API calls
- **APScheduler** - Task scheduling for score updates
- **JWT** - Authentication for admin access

### Frontend
- **React 18** with **TypeScript** - Modern UI framework
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Data fetching and caching
- **React Router** - Client-side routing

### Infrastructure
- **Railway/Render** - Backend hosting
- **Vercel** - Frontend hosting
- **Supabase** - PostgreSQL database hosting

## 📁 Project Structure

```
masters/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── config.py       # Configuration management
│   │   ├── database.py     # Database connection
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── api/            # API routes
│   │   │   ├── public/    # Public endpoints
│   │   │   └── admin/     # Admin endpoints
│   │   ├── services/       # Business logic
│   │   │   ├── scoring.py # Scoring engine
│   │   │   ├── api_client.py # Slash Golf API client
│   │   │   └── import_service.py # SmartSheet import
│   │   └── utils/          # Utility functions
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API client
│   │   ├── types/         # TypeScript types
│   │   └── App.tsx        # Main app component
│   ├── public/            # Static assets
│   ├── package.json       # Node dependencies
│   └── .env.example       # Environment variables template
│
├── docs/                   # Additional documentation
├── ARCHITECTURE.md         # Detailed architecture plan
├── DEVELOPMENT_PLAN.md     # Phased development plan
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL database (or Supabase account)
- Slash Golf API key (RapidAPI)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd masters
   ```

2. **Set up Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Set up Database**
   ```bash
   # Create database (if using local PostgreSQL)
   createdb eldorado_masters
   
   # Run migrations
   alembic upgrade head
   ```

4. **Set up Frontend**
   ```bash
   cd frontend
   npm install
   cp .env.example .env
   # Edit .env with your API URL
   ```

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/eldorado_masters

# Slash Golf API
SLASH_GOLF_API_KEY=your_rapidapi_key
SLASH_GOLF_API_HOST=live-golf-data.p.rapidapi.com

# JWT
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

## 💻 Development

### Running the Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Running the Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:5173`

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
pytest tests/test_scoring.py -v  # Run specific test file
pytest --cov=app tests/          # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Test Scripts

All test scripts are located in:
- Backend: `backend/tests/`
- Frontend: `frontend/src/__tests__/`

See [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) for detailed test requirements for each phase.

## 📊 Scoring Rules

### Daily Scoring

**Thursday (Round 1)**
- Tournament Leader: 8 points
- Top 5: 5 points
- Top 10: 3 points
- Top 25: 1 point

**Friday & Saturday (Rounds 2 & 3)**
- Tournament Leader: 12 points
- Top 5: 8 points
- Top 10: 5 points
- Top 25: 3 points
- Made cut, outside top 25: 1 point

**Sunday (Round 4)**
- Tournament Winner: 15 points
- Tournament Leader (if not winner): 12 points
- Top 5: 8 points
- Top 10: 5 points
- Top 25: 3 points
- Made cut, outside top 25: 1 point

### Bonus Points

- **Greens in Regulation Leader** (per day): 1 point
- **Fairways Hit Leader** (per day): 1 point
- **Low Score of Day**: 1 point
- **Eagles** (per day): 2 points
- **Double Eagle**: 3 points
- **Hole in One**: 3 points (eagle 2 + bonus 1)
- **All 6 Make Weekend**: 5 points (forfeited if rebuy)

### Re-buy Rules

**Missed Cut Re-buy ($25)**
- Original player's Thursday/Friday points remain
- Re-buy player earns points from Saturday/Sunday only
- Weekend bonus still eligible

**Underperformer Re-buy ($25)**
- Original player's Thursday/Friday points remain
- Weekend bonus (5 points) is FORFEITED
- Re-buy player earns points from Saturday/Sunday only

## 🚢 Deployment

### Backend Deployment (Railway)

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Railway will automatically deploy on push to main

### Frontend Deployment (Vercel)

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Vercel will automatically deploy on push to main

### Database (Supabase)

1. Create a new Supabase project
2. Get connection string
3. Update `DATABASE_URL` in backend environment variables
4. Run migrations: `alembic upgrade head`

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

**Public:**
- `GET /api/leaderboard` - Current pool leaderboard
- `GET /api/entry/{entryId}` - Entry details
- `GET /api/tournament/current` - Current tournament info

**Admin:**
- `POST /api/admin/login` - Admin authentication
- `POST /api/admin/import-entries` - Import SmartSheet entries
- `POST /api/admin/import-rebuys` - Import SmartSheet rebuys

## 🔄 Development Phases

See [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) for the complete phased development approach.

**Quick Summary:**
1. Foundation & Setup
2. API Integration
3. Scoring Engine
4. Data Import
5. Frontend Foundation
6. Leaderboard & Display
7. Real-time Updates
8. Admin Interface
9. Testing & Polish
10. Deployment

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make your changes
3. Write/update tests
4. Run tests: `pytest` and `npm test`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 Notes

- **API Rate Limits**: Slash Golf API has rate limits (20,000 requests/day). The app implements caching to minimize API calls.
- **Data Retention**: All tournament data is stored. Purge policies can be configured later.
- **SmartSheet Format**: See admin documentation for expected SmartSheet column formats.

## 🆘 Support

For issues or questions:
1. Check the documentation in `docs/`
2. Review test scripts for examples
3. Check API documentation at `/docs` endpoint

## 📄 License

This project is for private use.

---

**Built with ❤️ for the Eldorado Masters Pool**
