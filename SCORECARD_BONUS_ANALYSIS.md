# Scorecard Bonus Points Analysis

## Current Situation

### ⚠️ **Eagles, Albatrosses, and Hole-in-Ones Are NOT Being Calculated**

**Why?**
- The scoring logic in `scoring.py` (lines 303-338) expects `scorecard_data` to calculate these bonuses
- However, `scorecard_data` is **never fetched** during tournament sync
- The `sync_tournament_data` method only fetches:
  1. Tournament info (1 API call)
  2. Leaderboard (1 API call)
  3. Players (from leaderboard data, no extra calls)

**Current Code Flow:**
```
sync_tournament_data()
  ├─ get_tournament() → 1 API call
  ├─ get_leaderboard() → 1 API call
  └─ save_score_snapshot(leaderboard_data, scorecard_data=None)
      └─ scorecard_data = {} (empty!)
```

**Result:**
- `scorecard_data` in the snapshot is always `{}` (empty dictionary)
- When calculating bonuses, the code checks `scorecard_data.get(player_id_str, [])` which returns `[]`
- No scorecard data = no eagle/albatross/hole-in-one bonuses are calculated

---

## What Would Be Required to Calculate These Bonuses

### API Calls Needed

To calculate eagles, albatrosses, and hole-in-ones, we need **hole-by-hole scorecard data** for each player.

**Current API Structure:**
- `/scorecard` endpoint requires: `playerId`, `orgId`, `tournId`, `year`
- **One API call per player** to get their scorecard

### Example Calculation

**Typical Tournament:**
- 150 players in the field
- 4 rounds
- Syncing every 5 minutes during active hours (6 AM - 11 PM = 17 hours)
- Active tournament days: 4 days

**API Calls for Scorecards:**
```
Per sync: 150 players × 1 call = 150 calls
Per hour: 150 calls × 12 syncs/hour = 1,800 calls
Per day: 1,800 calls × 17 hours = 30,600 calls
Per tournament: 30,600 calls × 4 days = 122,400 calls
```

**Plus existing calls:**
- Tournament info: ~1 call per sync
- Leaderboard: ~1 call per sync
- **Total: ~122,400 scorecard calls + ~1,000 other calls = ~123,400 calls per tournament**

---

## Optimization Strategies

### Option 1: Fetch Scorecards Only for Entry Players (Recommended)

**Strategy:**
- Only fetch scorecards for players who are in entries (not all 150 players)
- Cache scorecard data and only refetch if round has changed

**Example:**
- 50 entries × 6 players = 300 player entries
- But many players are duplicated across entries
- Unique players: ~50-100 players

**API Calls:**
```
Per sync: ~75 unique players × 1 call = 75 calls
Per hour: 75 calls × 12 syncs = 900 calls
Per day: 900 calls × 17 hours = 15,300 calls
Per tournament: 15,300 calls × 4 days = 61,200 calls
```

**Reduction: 50% fewer calls** (from 122,400 to 61,200)

### Option 2: Fetch Scorecards Only Once Per Round

**Strategy:**
- Fetch scorecards only when a round is completed (not every 5 minutes)
- Store scorecard data in database
- Reuse stored data for calculations

**API Calls:**
```
Per round: 75 unique players × 1 call = 75 calls
Per tournament: 75 calls × 4 rounds = 300 calls
```

**Reduction: 99.75% fewer calls** (from 122,400 to 300)

**Trade-off:**
- Bonuses calculated only after round completion
- Not real-time during the round

### Option 3: Smart Caching with Change Detection

**Strategy:**
- Fetch scorecards only for players whose scores have changed
- Use leaderboard data to detect which players have new scores
- Only fetch scorecards for players with updated scores

**API Calls:**
```
Per sync: ~10-20 players with changes × 1 call = 10-20 calls
Per hour: 20 calls × 12 syncs = 240 calls
Per day: 240 calls × 17 hours = 4,080 calls
Per tournament: 4,080 calls × 4 days = 16,320 calls
```

**Reduction: 87% fewer calls** (from 122,400 to 16,320)

**Trade-off:**
- More complex logic
- Need to track which players have updated scores

### Option 4: Batch API Endpoint (If Available)

**Strategy:**
- Check if Slash Golf API has a batch endpoint for scorecards
- Fetch multiple scorecards in one API call

**API Calls:**
```
If batch endpoint exists (e.g., 10 players per call):
Per sync: 75 players ÷ 10 = 8 calls
Per tournament: 8 calls × 12 syncs/hour × 17 hours × 4 days = 6,528 calls
```

**Reduction: 95% fewer calls** (from 122,400 to 6,528)

**Note:** Need to verify if Slash Golf API supports batch requests

---

## Recommended Implementation

### Phase 1: Basic Implementation (Option 1)
1. Fetch scorecards only for players in entries
2. Cache scorecard data per round
3. Only refetch if round has changed

**Estimated API Calls:**
- ~61,200 calls per tournament
- ~1,530 calls per day during tournament

### Phase 2: Optimization (Option 3)
1. Add change detection
2. Only fetch scorecards for players with updated scores
3. Use leaderboard data to detect changes

**Estimated API Calls:**
- ~16,320 calls per tournament
- ~408 calls per day during tournament

---

## Implementation Code Example

### Modified `sync_tournament_data` Method

```python
def sync_tournament_data(
    self,
    org_id: Optional[str] = None,
    tourn_id: Optional[str] = None,
    year: Optional[int] = None,
    fetch_scorecards: bool = True
) -> Dict[str, Any]:
    """
    Sync all tournament data.
    
    Args:
        fetch_scorecards: Whether to fetch scorecard data (default: True)
    """
    results = {
        "tournament": None,
        "players_synced": 0,
        "snapshot": None,
        "scorecards_fetched": 0,
        "errors": []
    }
    
    try:
        # Sync tournament
        tournament = self.sync_tournament(org_id, tourn_id, year)
        results["tournament"] = tournament
        
        # Get leaderboard
        leaderboard_data = self.api_client.get_leaderboard(org_id, tourn_id, year)
        
        # Sync players from leaderboard
        players = self.sync_players_from_leaderboard(leaderboard_data)
        results["players_synced"] = len(players)
        
        # Fetch scorecards if requested
        scorecard_data = {}
        if fetch_scorecards:
            # Get unique player IDs from entries
            from app.models import Entry
            entries = self.db.query(Entry).filter(
                Entry.tournament_id == tournament.id
            ).all()
            
            unique_player_ids = set()
            for entry in entries:
                unique_player_ids.update([
                    entry.player1_id, entry.player2_id, entry.player3_id,
                    entry.player4_id, entry.player5_id, entry.player6_id
                ])
                # Include rebuy players if they exist
                if entry.rebuy_player_ids:
                    unique_player_ids.update(entry.rebuy_player_ids)
            
            # Fetch scorecards for unique players
            for player_id in unique_player_ids:
                try:
                    scorecards = self.api_client.get_scorecard(
                        player_id=str(player_id),
                        org_id=org_id,
                        tourn_id=tourn_id,
                        year=year
                    )
                    scorecard_data[str(player_id)] = scorecards
                    results["scorecards_fetched"] += 1
                except Exception as e:
                    logger.warning(f"Failed to fetch scorecard for player {player_id}: {e}")
                    results["errors"].append(f"Scorecard fetch error for player {player_id}: {e}")
        
        # Save snapshot
        current_round = tournament.current_round or 1
        snapshot = self.save_score_snapshot(
            tournament_id=tournament.id,
            round_id=current_round,
            leaderboard_data=leaderboard_data,
            scorecard_data=scorecard_data if scorecard_data else None
        )
        results["snapshot"] = snapshot
        
        logger.info(f"Successfully synced tournament {tournament.name}")
        
    except Exception as e:
        error_msg = f"Error syncing tournament data: {e}"
        logger.error(error_msg)
        results["errors"].append(error_msg)
        self.db.rollback()
    
    return results
```

---

## Summary

### Current State
- ✅ Eagles, albatrosses, and hole-in-ones are **NOT being calculated**
- ✅ No extra API calls are being made for scorecards
- ⚠️ These bonus points are silently not awarded

### If We Implement Scorecard Fetching
- **Option 1 (Basic)**: ~61,200 calls per tournament
- **Option 2 (Once per round)**: ~300 calls per tournament (but not real-time)
- **Option 3 (Smart caching)**: ~16,320 calls per tournament
- **Option 4 (Batch API)**: ~6,528 calls per tournament (if available)

### Recommendation
1. **Short term**: Document that these bonuses are not currently calculated
2. **Medium term**: Implement Option 1 (fetch only for entry players)
3. **Long term**: Optimize with Option 3 (smart caching with change detection)

---

*Last Updated: January 2026*
