# Scoring Logic Validation

## Current Implementation vs. Rules

### ✅ CORRECT: Point Values

**Round 1 (Thursday)**:
- ✅ Tournament Leader = 8 points
- ✅ Players in top 5 = 5 points
- ✅ Players in top 10 = 3 points
- ✅ Players in top 25 = 1 point

**Round 2 & 3 (Friday & Saturday)**:
- ✅ Tournament leader = 12 points
- ✅ Players in top 5 = 8 points
- ✅ Players in top 10 = 5 points
- ✅ Players in top 25 = 3 points
- ⚠️ Make cut, outside top 25 = 1 pt. (see issue below)

**Round 4 (Sunday)**:
- ✅ Tournament winner = 15 points
- ✅ Tournament leader (if not winner) = 12 points
- ✅ Players in top 5 = 8 points
- ✅ Players in top 10 = 5 points
- ✅ Players in top 25 = 3 points
- ⚠️ Make cut, outside top 25 = 1 pt. (see issue below)

### ✅ CORRECT: Tie Handling

The code correctly handles ties:
- Tied positions like "T4" are parsed by stripping the "T" (line 95)
- All tied players get the same position number
- Example: 4 players at T4 all get position 4, which means they all get top_5 points (5 points)
- ✅ This matches the rule: "if 4 players finish a day T4, all 4 will earn the point value for a top 5 daily finish"

### ⚠️ ISSUE: "Made Cut" Logic

**Problem**: The current code gives 1 point to ANY player with position > 25 in rounds 2-4, without checking if they actually made the cut.

**Current Code** (line 115-117):
```python
elif round_id >= 2 and rules.get("made_cut"):
    # Made cut but outside top 25 (Friday-Sunday only)
    return float(rules.get("made_cut", 0))
```

**Issue**: This doesn't verify the player's status. If a player has position 30 but status "cut", they would still get 1 point.

**Rule**: "Make cut, outside top 25 = 1 pt." - This should only apply to players who actually made the cut.

**Fix Needed**: Check player status before awarding "made_cut" points. Players with status "cut", "wd", or "dq" should get 0 points, not 1 point.

### ✅ CORRECT: Sunday Winner Logic

- Winner is determined as position 1 with status "complete" (line 189)
- Winner gets 15 points (line 103-104)
- Leader (position 1) who is not the winner gets 12 points

## Summary

**What's Correct**:
1. ✅ All point values match the rules
2. ✅ Tie handling works correctly
3. ✅ Sunday winner logic is correct
4. ✅ Round-specific scoring is correct

**What Needs Fixing**:
1. ⚠️ "Made cut" points should only be awarded to players who actually made the cut (status not "cut", "wd", or "dq")
