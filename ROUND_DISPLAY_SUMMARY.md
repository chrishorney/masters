# Round Display & Per-Player Points Summary

## Current Round Display

The current round is now displayed on all relevant pages:

### ✅ Pages with Current Round Display

1. **HomePage** (`/`)
   - Shows: `Round {tournament.current_round} • {tournament.status}`
   - Location: Hero section below tournament name

2. **LeaderboardPage** (`/leaderboard`)
   - Shows: `{tournamentInfo.name} • Round {tournamentInfo.current_round}`
   - Location: Page header

3. **EntryDetailPage** (`/entry/{id}`)
   - Shows: `{tournament.name} • Round {tournament.current_round}` in header
   - Shows: `(Current)` indicator next to active round in round-by-round table
   - Location: Page header and round tables

4. **AdminPage** (`/admin`)
   - Shows: `Managing: {tournament.name} • Round {tournament.current_round}`
   - Location: Page header

5. **Layout Component** (All pages)
   - Shows: `Round {tournament.current_round} • {tournament.status}`
   - Location: Navigation bar (desktop and mobile)

6. **RankingHistoryPage** (`/ranking-history`)
   - Shows: Round filter dropdown (1-4)
   - Uses current round for default filtering

### ✅ All Round Displays Use Dynamic Data

- All displays use `tournament.current_round` from API
- No hardcoded round values
- Updates automatically when sync runs

---

## Per-Player Points Per Round

### New Features on EntryDetailPage

#### 1. **Player Points Per Round Section**

Shows detailed breakdown for each round:
- **Player Name**: Shows original or rebuy player name
- **Position**: Player's position in that round
- **Base Points**: Position-based points earned
- **Bonus Points**: All bonus points earned (with types listed)
- **Round Total**: Base + Bonus for that player in that round

**Rebuy Handling:**
- Rounds 1-2: Shows original 6 players
- Rounds 3-4: Shows rebuy players if they exist, otherwise original players
- Displays "Rebuy (was [original player])" for rebuy players

#### 2. **Player Totals (All Rounds) Section**

Aggregates points across all rounds:
- **Player Name**: Original or rebuy player
- **Rounds Played**: Which rounds this player participated in (e.g., "1, 2, 3")
- **Total Base Points**: Sum of all base points across rounds
- **Total Bonus Points**: Sum of all bonus points across rounds
- **Total Points**: Grand total for this player

**Key Features:**
- Shows all players (original + rebuy)
- Properly aggregates only rounds where player was active
- Accounts for rebuys (original player points from rounds 1-2, rebuy player points from rounds 3-4)
- Sorted by total points (highest first)

---

## Data Flow

### Backend → Frontend

1. **Sync Tournament** (`/api/tournament/sync`)
   - Gets `currentRound` from Slash Golf API
   - Stores in `tournaments.current_round`
   - Creates `ScoreSnapshot` with `round_id = current_round`

2. **Calculate Scores** (`/api/scores/calculate`)
   - Uses `tournament.current_round` to determine which round to calculate
   - Creates `DailyScore` records with:
     - `round_id`: Round number
     - `base_points`: Position-based points
     - `bonus_points`: All bonus points
     - `details.base_breakdown`: Per-player breakdown
     - `details.bonuses`: List of bonus points

3. **Get Entry Details** (`/api/entry/{id}`)
   - Returns all `DailyScore` records (one per round)
   - Returns all `BonusPoint` records
   - Returns tournament with `current_round`

4. **Frontend Display**
   - Shows current round from `tournament.current_round`
   - Shows per-round scores from `daily_scores` array
   - Shows per-player breakdown from `score.details.base_breakdown`
   - Aggregates player totals across all rounds

---

## Round Logic

### How Rounds Are Determined

1. **From API**: `currentRound` comes from Slash Golf API
2. **Stored**: Saved in `tournaments.current_round` column
3. **Used**: All calculations and displays use this value

### Rebuy Logic

**Rounds 1-2:**
- Always use original 6 players
- Points go to original players

**Rounds 3-4:**
- If rebuy exists: Use rebuy players (replacing original players)
- If no rebuy: Use original players
- Points go to active players (rebuy or original)

**Aggregation:**
- Original players: Points from rounds 1-2 (and 3-4 if no rebuy)
- Rebuy players: Points from rounds 3-4 only
- Total entry points: Sum of all active players' points

---

## Example Display

### EntryDetailPage Structure

```
Entry Header
├─ Tournament Name • Round 2

Summary Cards
├─ Total Points: 45.0
├─ Base Points: 38.0
└─ Bonus Points: 7.0

Selected Players
└─ 6 players listed (with rebuy info if applicable)

Round-by-Round Scores (Summary)
├─ Round 1: 12.0 pts (Base: 10.0, Bonus: 2.0)
├─ Round 2: 15.0 pts (Base: 12.0, Bonus: 3.0) [Current]
└─ Total: 27.0 pts

Player Points Per Round
├─ Round 1
│  ├─ Player 1: Position 5, Base: 5.0, Bonus: 0.0, Total: 5.0
│  ├─ Player 2: Position 10, Base: 3.0, Bonus: 2.0, Total: 5.0
│  └─ ... (all 6 players)
├─ Round 2 [Current]
│  ├─ Player 1: Position 3, Base: 8.0, Bonus: 1.0, Total: 9.0
│  └─ ... (all 6 players)
└─ ... (all rounds)

Player Totals (All Rounds)
├─ Player 1: Rounds 1,2 | Base: 13.0, Bonus: 1.0, Total: 14.0
├─ Player 2: Rounds 1,2 | Base: 8.0, Bonus: 2.0, Total: 10.0
└─ ... (all players, sorted by total)

Bonus Points Breakdown
└─ All bonus points with player, type, round, and points
```

---

## Validation

### Check Current Round

1. **API Endpoint**: `/api/tournament/current`
   - Returns: `current_round: 2`

2. **Validation Endpoint**: `/api/validation/sync-status`
   - Returns: Tournament info with `current_round`
   - Validates: `current_round_matches_latest_snapshot`

3. **Frontend**: All pages show `Round 2` (or current round)

### Check Per-Player Points

1. **Entry Detail Page**: `/entry/{id}`
   - Shows per-player breakdown per round
   - Shows player totals across all rounds
   - Accounts for rebuys correctly

2. **Data Source**: `DailyScore.details.base_breakdown`
   - Contains: `{player1: {player_id, position, points}, ...}`

---

## Summary

✅ **Current Round Display**: Added to all relevant pages  
✅ **Per-Player Per-Round**: Detailed breakdown showing each player's points per round  
✅ **Player Aggregation**: Total points per player across all rounds  
✅ **Rebuy Handling**: Correctly shows which players were active in each round  
✅ **Current Round Indicator**: Shows "(Current)" next to active round  
✅ **End-of-Day Points**: All points (base + bonus) are logged per round in `DailyScore` table  

The system now provides complete visibility into:
- Which round the tournament is currently in
- How many points each player earned in each round
- Total points per player across all rounds
- Which players were active in which rounds (accounting for rebuys)

---

*Last Updated: January 2026*
