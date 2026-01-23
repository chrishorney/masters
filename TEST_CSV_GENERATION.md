# Test CSV Generation Guide

This guide explains how to clear all entries and generate a new test CSV file with 3 users and random players.

## Quick Start

### Prerequisites

Make sure you have the `requests` module installed:
```bash
pip3 install requests
```

Or if you're using the backend's virtual environment:
```bash
cd backend
pip install requests
```

### Option 1: Sync and Generate (Recommended)

If tournament data hasn't been synced yet, use this script:

```bash
cd backend
./sync_and_generate_csv.sh
```

This will:
1. Sync tournament 2 data from the API
2. Generate the test CSV file

### Option 2: Manual Steps

### 1. Sync Tournament Data (if needed)

First, make sure tournament data is synced:
```bash
curl -X POST "https://masters-production.up.railway.app/api/tournament/sync?year=2026"
```

### 2. Generate Test CSV

```bash
cd backend
python3 generate_test_csv.py \
  --tournament-id 2 \
  --api-url https://masters-production.up.railway.app \
  --output test_entries.csv
```

This will:
- Fetch all players from tournament 2
- Generate a CSV with 3 test users
- Each user gets 6 random players from the tournament
- Save to `test_entries.csv`

### 2. Clear Existing Entries

```bash
curl -X POST "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2/clear-entries?confirm=true"
```

**⚠️ WARNING: This deletes all entries for tournament 2!**

### 3. Import New CSV

```bash
curl -X POST "https://masters-production.up.railway.app/api/admin/import/entries" \
  -F "tournament_id=2" \
  -F "file=@test_entries.csv"
```

## Script Options

```bash
python3 generate_test_csv.py [OPTIONS]

Options:
  --tournament-id ID    Tournament ID (default: 2)
  --api-url URL         API base URL (default: http://localhost:8000)
  --output FILE         Output CSV file (default: test_entries.csv)
  --num-users N         Number of test users (default: 3)
```

## Example Output

The generated CSV will look like:

```csv
Participant Name,Player 1 Name,Player 2 Name,Player 3 Name,Player 4 Name,Player 5 Name,Player 6 Name
Test User 1,Scottie Scheffler,Jon Rahm,Viktor Hovland,Jordan Spieth,Dustin Johnson,Brooks Koepka
Test User 2,Collin Morikawa,Sam Burns,Peter Malnati,Cameron Young,Xander Schauffele,Patrick Cantlay
Test User 3,Rory McIlroy,Justin Thomas,Tony Finau,Max Homa,Tommy Fleetwood,Shane Lowry
```

## Complete Workflow

```bash
# 1. Generate CSV
python3 backend/generate_test_csv.py \
  --tournament-id 2 \
  --api-url https://masters-production.up.railway.app

# 2. Clear existing entries
curl -X POST "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2/clear-entries?confirm=true"

# 3. Import new entries
curl -X POST "https://masters-production.up.railway.app/api/admin/import/entries" \
  -F "tournament_id=2" \
  -F "file=@test_entries.csv"

# 4. Verify
curl "https://masters-production.up.railway.app/api/admin/diagnostics/tournament/2"
```

## Notes

- Players are selected randomly from the tournament leaderboard
- Each user gets 6 unique players (no duplicates within an entry)
- Player names use the format from the tournament leaderboard
- The script requires tournament data to be synced first

## Troubleshooting

**Error: "No players found"**
- Make sure tournament data is synced: `POST /api/tournament/sync?year=2026`

**Error: "Need at least 6 players"**
- Tournament doesn't have enough players in leaderboard
- Sync tournament data first

**Import fails with "Player not found"**
- Player names might not match exactly
- Check player names in the generated CSV match the leaderboard format
