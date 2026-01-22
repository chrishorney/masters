# Eldorado Masters Pool - Architecture Plan

## Overview
A near real-time web application for managing and displaying a Masters Golf Tournament pool with complex scoring rules, bonus points, and re-buy functionality.

## Technology Stack

### Backend
- **Framework**: FastAPI (Python) - Modern, fast, async-capable, great for learning Python
- **Database**: PostgreSQL (via Supabase or Railway)
- **ORM**: SQLAlchemy
- **API Client**: httpx (async HTTP client)
- **Authentication**: JWT tokens for admin access
- **Task Queue**: Celery (for background score updates) or simple scheduled tasks

### Frontend
- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS (modern, responsive)
- **State Management**: React Query (for data fetching and caching)
- **Real-time Updates**: WebSocket or polling (every 1-2 minutes during tournament)
- **Hosting**: Vercel (free tier, excellent for React)

### Infrastructure
- **Backend Hosting**: Railway or Render (Python-friendly, easy deployment)
- **Database**: Supabase PostgreSQL (free tier, includes REST API)
- **Environment Variables**: `.env` files (never commit to Git)

## System Architecture

```
┌─────────────────┐
│   React Frontend │  (Vercel)
│   (Public View)  │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────┐
│  FastAPI Backend│  (Railway/Render)
│  - Admin Auth   │
│  - API Routes   │
│  - Scoring Logic│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐  ┌──▼────────┐
│PostgreSQL│ │Slash Golf│
│ Database │ │   API    │
└─────────┘ └──────────┘
```

## Data Models

### Core Entities

1. **Tournament**
   - id, year, tournId, name, startDate, endDate, status
   - orgId (PGA = 1)

2. **Participant**
   - id, name, email (optional), entryDate, paid (boolean)

3. **Entry**
   - id, participantId, tournamentId
   - player1Id, player2Id, player3Id, player4Id, player5Id, player6Id
   - rebuyPlayerIds (JSON array)
   - rebuyType (null, "missed_cut", "underperformer")
   - weekendBonusEarned (boolean)

4. **Player** (from API, cached)
   - playerId, firstName, lastName

5. **ScoreSnapshot**
   - id, tournamentId, roundId, timestamp
   - leaderboardData (JSON)
   - scorecardData (JSON)

6. **DailyScore**
   - id, entryId, roundId, date
   - basePoints, bonusPoints, totalPoints
   - details (JSON - breakdown of scoring)

7. **BonusPoints**
   - id, entryId, roundId, bonusType, points
   - bonusType: "gir_leader", "fairways_leader", "low_score", "eagle", "double_eagle", "hole_in_one", "all_make_cut"

## API Endpoints

### Public Endpoints (No Auth)
- `GET /api/leaderboard` - Current pool leaderboard
- `GET /api/entry/{entryId}` - Entry details
- `GET /api/tournament/current` - Current tournament info
- `GET /api/scores/live` - Live scoring updates

### Admin Endpoints (JWT Auth)
- `POST /api/admin/login` - Admin authentication
- `POST /api/admin/import-entries` - Import SmartSheet entries (CSV/JSON)
- `POST /api/admin/import-rebuys` - Import SmartSheet rebuys
- `POST /api/admin/refresh-scores` - Manually trigger score refresh
- `GET /api/admin/participants` - List all participants
- `GET /api/admin/entries` - List all entries

## Scoring Logic Engine

### Daily Scoring Rules

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

1. **Greens in Regulation Leader** (per day): 1 point
2. **Fairways Hit Leader** (per day): 1 point
3. **Low Score of Day**: 1 point
4. **Eagles** (per day): 2 points
5. **Double Eagle**: 3 points
6. **Hole in One**: 3 points (eagle 2 + bonus 1)
7. **All 6 Make Weekend**: 5 points (forfeited if rebuy)

### Re-buy Logic

**Missed Cut Re-buy:**
- Original player's Thursday/Friday points remain
- Re-buy player earns points from Saturday/Sunday only
- Weekend bonus still eligible if all 6 (including rebuys) make cut

**Underperformer Re-buy:**
- Original player's Thursday/Friday points remain
- Weekend bonus (5 points) is FORFEITED
- Re-buy player earns points from Saturday/Sunday only

## Real-time Update Strategy

1. **Polling Schedule:**
   - During tournament: Every 1-2 minutes
   - Off-season: Daily check for new tournaments

2. **Update Process:**
   - Fetch leaderboard from Slash Golf API
   - Fetch scorecards for all tracked players
   - Calculate scores for all entries
   - Store snapshot in database
   - Push update to frontend (WebSocket or SSE)

3. **Background Jobs:**
   - Celery worker or scheduled task (cron-like)
   - Runs continuously during tournament days

## SmartSheet Import Format

### Entries Import (Expected Columns)
- Participant Name
- Player 1 Name
- Player 2 Name
- Player 3 Name
- Player 4 Name
- Player 5 Name
- Player 6 Name

### Rebuys Import (Expected Columns)
- Participant Name (or Entry ID)
- Original Player Name
- Rebuy Player Name
- Rebuy Type ("missed_cut" or "underperformer")

## Security Considerations

1. **API Key Protection**: Store in environment variables, never in code
2. **Admin Authentication**: JWT tokens with expiration
3. **Rate Limiting**: Respect Slash Golf API rate limits (20,000 requests/day)
4. **Input Validation**: Validate all SmartSheet imports
5. **SQL Injection**: Use ORM (SQLAlchemy) to prevent

## Performance Optimizations

1. **Caching**: Cache leaderboard data for 30-60 seconds
2. **Database Indexing**: Index on entryId, tournamentId, roundId
3. **Batch Updates**: Update multiple entries in single transaction
4. **Frontend Caching**: React Query for client-side caching

## Deployment Strategy

1. **Development**: Local with Docker Compose
2. **Staging**: Separate environment for testing
3. **Production**: Railway/Render backend + Vercel frontend

## Monitoring & Logging

1. **Error Tracking**: Sentry (optional, free tier)
2. **Logging**: Python logging to files/cloud
3. **Health Checks**: `/health` endpoint
4. **API Monitoring**: Track Slash Golf API usage
