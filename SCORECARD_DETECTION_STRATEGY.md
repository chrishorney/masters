# Scorecard Detection Strategy - Analysis & Implementation Plan

## User's Suggestion Summary

**Approach:**
1. Fetch leaderboard every 5 min (already doing this)
2. Store leaderboard in ScoreSnapshot (already doing this)
3. Compare current leaderboard to previous snapshot
4. If player's `currentRoundScore` improved by 2+ strokes → fetch their scorecard
5. Determine which bonus (eagle/albatross/hole-in-one) and award points

**Benefits:**
- ✅ Only fetch scorecards when needed (eagle/albatross/hole-in-one detected)
- ✅ Dramatically reduces API calls (from ~122,400 to ~50-200 per tournament)
- ✅ Real-time detection during active rounds
- ✅ Uses existing infrastructure (ScoreSnapshot)

---

## Analysis: Potential Issues & Solutions

### ✅ Issue 1: Score Format Parsing

**Problem:**
- `currentRoundScore` is a string: "-5", "+2", "E", or empty
- Need to parse and compare correctly

**Solution:**
```python
def parse_round_score(score_str: str) -> Optional[int]:
    """Parse currentRoundScore string to integer."""
    if not score_str or score_str == "":
        return None
    if score_str.startswith("-"):
        return -int(score_str[1:])
    elif score_str.startswith("+"):
        return int(score_str[1:])
    elif score_str == "E":
        return 0
    return None
```

### ✅ Issue 2: Round Changes

**Problem:**
- When round changes (e.g., Round 1 → Round 2), we shouldn't compare scores across rounds
- Need to detect round changes and reset comparison baseline

**Solution:**
- Only compare snapshots with the same `round_id`
- When round changes, previous snapshot for that round becomes the baseline
- Track round changes in the comparison logic

### ✅ Issue 3: Multiple Improvements in One Sync

**Problem:**
- Player could improve by 4 strokes (2 eagles, or 1 albatross, or 1 eagle + 1 birdie)
- Need to check scorecard to see which holes had the improvements

**Solution:**
- Always fetch scorecard when improvement ≥ 2 strokes
- Parse scorecard to find all holes with score_to_par ≤ -2
- Award bonuses for each qualifying hole

### ✅ Issue 4: Player Status Edge Cases

**Problem:**
- Player might be "WD" (withdrawn), "DQ" (disqualified), or not started
- `currentRoundScore` might be empty or invalid

**Solution:**
- Skip comparison if:
  - `status` is "WD", "DQ", or "cut"
  - `currentRoundScore` is empty or invalid
  - Player hasn't started the round yet

### ✅ Issue 5: Scorecard Data Structure

**Problem:**
- Need to understand scorecard structure to find which hole had the improvement
- Scorecard might have multiple rounds

**Solution:**
- Scorecard is a list of rounds
- Each round has `holes` dict with hole numbers as keys
- Each hole has `holeScore` and `par`
- Compare current scorecard to previous to find new improvements

### ⚠️ Issue 6: Previous Scorecard Not Available

**Problem:**
- We're comparing leaderboard scores, but to find which hole improved, we need previous scorecard
- First time detecting improvement, we won't have previous scorecard

**Solution:**
- **Option A**: Always fetch full scorecard and compare all holes
- **Option B**: Store previous scorecard in snapshot for comparison
- **Option C**: Parse scorecard to find holes with score_to_par ≤ -2 (simpler)

**Recommendation: Option C** - When we detect improvement ≥ 2 strokes, fetch scorecard and check all holes for eagles/albatrosses/hole-in-ones. Award bonuses for any qualifying holes that haven't been awarded yet.

### ✅ Issue 7: Duplicate Bonus Detection

**Problem:**
- Same eagle/albatross/hole-in-one could be detected multiple times
- Need to track which bonuses have already been awarded

**Solution:**
- Store bonus points in database with `hole` number
- Before awarding, check if bonus already exists for that player/round/hole
- Use `BonusPoint` model to track awarded bonuses

---

## Implementation Plan

### Step 1: Add Score Comparison Logic

**Location:** `backend/app/services/data_sync.py`

**New Method:**
```python
def detect_scorecard_changes(
    self,
    tournament_id: int,
    current_leaderboard: Dict[str, Any],
    current_round: int
) -> List[Dict[str, Any]]:
    """
    Compare current leaderboard to previous snapshot and detect players
    who improved by 2+ strokes (potential eagle/albatross/hole-in-one).
    
    Returns:
        List of player IDs that need scorecard fetching
    """
    # Get previous snapshot for same round
    previous_snapshot = self.db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id,
        ScoreSnapshot.round_id == current_round
    ).order_by(ScoreSnapshot.timestamp.desc()).offset(1).first()
    
    if not previous_snapshot:
        # First snapshot for this round, no comparison possible
        return []
    
    previous_leaderboard = previous_snapshot.leaderboard_data
    players_to_fetch = []
    
    # Build maps of player_id -> currentRoundScore
    current_scores = {}
    previous_scores = {}
    
    for row in current_leaderboard.get("leaderboardRows", []):
        player_id = str(row.get("playerId"))
        status = row.get("status", "").lower()
        score_str = row.get("currentRoundScore", "")
        
        # Skip if player hasn't started or is withdrawn/disqualified
        if status in ["wd", "dq", "cut"] or not score_str:
            continue
        
        current_scores[player_id] = self._parse_round_score(score_str)
    
    for row in previous_leaderboard.get("leaderboardRows", []):
        player_id = str(row.get("playerId"))
        score_str = row.get("currentRoundScore", "")
        if score_str:
            previous_scores[player_id] = self._parse_round_score(score_str)
    
    # Compare scores
    for player_id, current_score in current_scores.items():
        if current_score is None:
            continue
        
        previous_score = previous_scores.get(player_id)
        if previous_score is None:
            # Player just started, can't compare
            continue
        
        score_improvement = previous_score - current_score  # Negative = better score
        
        # If improved by 2+ strokes, fetch scorecard
        if score_improvement >= 2:
            players_to_fetch.append({
                "player_id": player_id,
                "previous_score": previous_score,
                "current_score": current_score,
                "improvement": score_improvement
            })
    
    return players_to_fetch
```

### Step 2: Fetch Scorecards for Detected Players

**Location:** `backend/app/services/data_sync.py`

**Modify `sync_tournament_data`:**
```python
def sync_tournament_data(
    self,
    org_id: Optional[str] = None,
    tourn_id: Optional[str] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    # ... existing code ...
    
    # Get leaderboard
    leaderboard_data = self.api_client.get_leaderboard(org_id, tourn_id, year)
    
    # Detect players who need scorecard fetching
    current_round = tournament.current_round or 1
    players_to_fetch = self.detect_scorecard_changes(
        tournament_id=tournament.id,
        current_leaderboard=leaderboard_data,
        current_round=current_round
    )
    
    # Fetch scorecards for detected players
    scorecard_data = {}
    for player_info in players_to_fetch:
        player_id = player_info["player_id"]
        try:
            scorecards = self.api_client.get_scorecard(
                player_id=player_id,
                org_id=org_id,
                tourn_id=tourn_id,
                year=year
            )
            scorecard_data[player_id] = scorecards
            logger.info(f"Fetched scorecard for player {player_id} (improvement: {player_info['improvement']} strokes)")
        except Exception as e:
            logger.warning(f"Failed to fetch scorecard for player {player_id}: {e}")
            results["errors"].append(f"Scorecard fetch error for player {player_id}: {e}")
    
    # Save snapshot with scorecard data
    snapshot = self.save_score_snapshot(
        tournament_id=tournament.id,
        round_id=current_round,
        leaderboard_data=leaderboard_data,
        scorecard_data=scorecard_data if scorecard_data else None
    )
    
    # ... rest of existing code ...
```

### Step 3: Update Bonus Point Calculation

**Location:** `backend/app/services/scoring.py`

**Modify `calculate_bonus_points`:**
- Already handles scorecard data correctly
- Will automatically detect eagles/albatrosses/hole-in-ones from fetched scorecards
- Need to ensure we don't award duplicates

**Add duplicate check:**
```python
# Before awarding bonus, check if it already exists
existing_bonus = self.db.query(BonusPoint).filter(
    BonusPoint.entry_id == entry.id,
    BonusPoint.round_id == round_id,
    BonusPoint.bonus_type == bonus["bonus_type"],
    BonusPoint.player_id == bonus.get("player_id"),
    BonusPoint.hole == bonus.get("hole")  # Add hole to BonusPoint model if not exists
).first()

if not existing_bonus:
    # Award bonus
```

### Step 4: Add Hole Tracking to BonusPoint Model

**Location:** `backend/app/models/bonus_point.py`

**Add `hole` field:**
```python
hole = Column(Integer, nullable=True)  # Hole number for eagle/albatross/hole-in-one
```

**Migration needed:**
- Add `hole` column to `bonus_points` table
- Make it nullable (not all bonuses have holes)

---

## Expected API Call Reduction

### Before (Naive Approach):
- 150 players × 1 call = 150 calls per sync
- 12 syncs/hour × 17 hours/day × 4 days = 122,400 calls per tournament

### After (Smart Detection):
- **Typical tournament**: ~5-10 eagles/albatrosses/hole-in-ones per round
- **4 rounds**: ~20-40 total events
- **Per sync**: ~0-2 players need scorecard fetching
- **Total**: ~50-200 calls per tournament

**Reduction: 99.8% fewer calls!** 🎉

---

## Edge Cases Handled

✅ **Round Changes**: Only compare within same round  
✅ **Player Status**: Skip WD/DQ/not started  
✅ **Score Parsing**: Handle "-5", "+2", "E", empty strings  
✅ **Multiple Improvements**: Check all holes in scorecard  
✅ **Duplicate Bonuses**: Track by player/round/hole  
✅ **First Snapshot**: No comparison, no false positives  
✅ **API Failures**: Graceful degradation, log errors  

---

## Testing Strategy

### Unit Tests:
1. Test score parsing (`_parse_round_score`)
2. Test comparison logic (2+ stroke improvement)
3. Test edge cases (WD, DQ, round changes)

### Integration Tests:
1. Test full flow: sync → detect → fetch → calculate
2. Test with real tournament data
3. Test duplicate bonus prevention

### Manual Tests:
1. Run during live tournament
2. Verify bonuses are awarded correctly
3. Verify API calls are minimal

---

## Implementation Checklist

- [ ] Add `_parse_round_score` helper method
- [ ] Add `detect_scorecard_changes` method
- [ ] Modify `sync_tournament_data` to use detection
- [ ] Add `hole` field to `BonusPoint` model
- [ ] Create database migration for `hole` field
- [ ] Update bonus calculation to check duplicates by hole
- [ ] Add logging for scorecard fetches
- [ ] Add unit tests
- [ ] Test with live tournament data

---

## Summary

**Your suggestion is excellent!** It's a smart optimization that:
- ✅ Dramatically reduces API calls (99.8% reduction)
- ✅ Uses existing infrastructure
- ✅ Detects bonuses in real-time
- ✅ Handles edge cases properly

**Minor considerations:**
- Need to handle round changes (only compare same round)
- Need to track holes to prevent duplicate bonuses
- Need robust score parsing

**Recommendation:** Implement this approach! It's much better than fetching all scorecards.

---

*Last Updated: January 2026*
