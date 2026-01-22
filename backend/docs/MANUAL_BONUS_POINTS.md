# Manual Bonus Points Guide (GIR & Fairways)

## Overview

GIR (Greens in Regulation) and Fairways Hit leader bonuses need to be added manually since they're not available in the API data. This guide shows you how to add them quickly and easily.

## How It Works

1. **Add Bonus Point**: Use the admin endpoint to add a GIR or Fairways bonus for a specific player
2. **Automatic Distribution**: The system automatically finds all entries that have that player
3. **Automatic Recalculation**: Scores are automatically recalculated for all affected entries
4. **Persistent Storage**: Bonus points are stored in the database and included in all future calculations

## API Endpoints

### Add Single Bonus Point

**Endpoint:** `POST /api/admin/bonus-points/add`

**Request Body:**
```json
{
  "tournament_id": 1,
  "round_id": 1,
  "player_id": "50525",
  "bonus_type": "gir_leader",
  "points": 1.0
}
```

**Response:**
```json
{
  "message": "Bonus points added successfully",
  "bonus_type": "gir_leader",
  "round_id": 1,
  "player_id": "50525",
  "entries_found": 5,
  "bonus_points_created": 5,
  "scores_updated": 5
}
```

### Add Multiple Bonus Points (Bulk)

**Endpoint:** `POST /api/admin/bonus-points/add-bulk`

**Request Body:**
```json
{
  "tournament_id": 1,
  "round_id": 1,
  "bonuses": [
    {"player_id": "50525", "bonus_type": "gir_leader"},
    {"player_id": "47504", "bonus_type": "fairways_leader"}
  ]
}
```

### List Bonus Points

**Endpoint:** `GET /api/admin/bonus-points/list?tournament_id=1&round_id=1`

### Delete Bonus Point

**Endpoint:** `DELETE /api/admin/bonus-points/{bonus_point_id}`

## Finding Player IDs

### Option 1: Search by Name

**Endpoint:** `GET /api/admin/players/search?name=Morikawa`

**Response:**
```json
{
  "players": [
    {
      "player_id": "50525",
      "full_name": "Collin Morikawa",
      "first_name": "Collin",
      "last_name": "Morikawa"
    }
  ]
}
```

### Option 2: Get Tournament Players

**Endpoint:** `GET /api/admin/players/tournament/{tournament_id}`

Returns all players in the tournament's leaderboard with their IDs.

## Example Workflow

### Step 1: Find the Player ID
```bash
curl "http://localhost:8000/api/admin/players/search?name=Morikawa"
```

### Step 2: Add GIR Leader Bonus
```bash
curl -X POST "http://localhost:8000/api/admin/bonus-points/add" \
  -H "Content-Type: application/json" \
  -d '{
    "tournament_id": 1,
    "round_id": 1,
    "player_id": "50525",
    "bonus_type": "gir_leader",
    "points": 1.0
  }'
```

### Step 3: Add Fairways Leader Bonus
```bash
curl -X POST "http://localhost:8000/api/admin/bonus-points/add" \
  -H "Content-Type: application/json" \
  -d '{
    "tournament_id": 1,
    "round_id": 1,
    "player_id": "47504",
    "bonus_type": "fairways_leader",
    "points": 1.0
  }'
```

### Step 4: Verify Bonus Points
```bash
curl "http://localhost:8000/api/admin/bonus-points/list?tournament_id=1&round_id=1"
```

## Using the API Documentation

The easiest way to use these endpoints is through the interactive API documentation:

1. Start the backend server: `uvicorn app.main:app --reload`
2. Visit: `http://localhost:8000/docs`
3. Navigate to the "admin" section
4. Use the interactive forms to add bonus points

## Important Notes

- **Automatic Updates**: When you add a bonus point, all entries with that player automatically get the bonus and scores are recalculated
- **Round-Specific**: Bonus points are specific to each round (Round 1, 2, 3, or 4)
- **Player Must Be in Entry**: The bonus only applies to entries that have that player in their lineup
- **Rebuy Handling**: If a player was rebought, the bonus applies to the rebuy player for rounds 3-4
- **Persistent**: Once added, bonus points persist and are included in all future score calculations

## Bonus Types

- `gir_leader`: Greens in Regulation leader (1 point)
- `fairways_leader`: Fairways Hit leader (1 point)

## Testing

You can test the manual bonus system with:

```bash
cd backend
source venv/bin/activate
python test_manual_bonus_points.py
```
