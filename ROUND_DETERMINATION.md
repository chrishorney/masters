# How Current Round is Determined

## Current Logic

**The `current_round` is NOT calculated from date/time - it comes directly from the Slash Golf API.**

### Flow:

1. **API Call**: `get_tournament()` calls Slash Golf API `/tournament` endpoint
2. **API Response**: API returns tournament data with `currentRound` field
3. **Parse**: Code extracts `currentRound` from API response:
   ```python
   tournament.current_round = parse_mongodb_value(api_data.get("currentRound", 1))
   ```
4. **Store**: Round is stored in database `tournaments.current_round` column
5. **Use**: All endpoints use `tournament.current_round` from database

### Key Points:

- ✅ **Round comes from API**, not calculated
- ✅ **Default is 1** if API doesn't provide `currentRound`
- ✅ **MongoDB format** is handled (e.g., `{"$numberInt": "2"}`)
- ⚠️ **If API returns Round 1**, database will show Round 1

## Why You Might See Round 1

### Possible Reasons:

1. **API Still Returning Round 1**
   - Slash Golf API might not have updated yet
   - Tournament might actually still be in Round 1
   - API might have a delay in updating

2. **API Field Name Different**
   - Field might be named differently (e.g., `current_round`, `round`, `roundNumber`)
   - Check raw API response

3. **MongoDB Format Not Parsed**
   - If API returns `{"$numberInt": "2"}`, `parse_mongodb_value()` should handle it
   - But if format is different, it might fail

4. **Sync Not Run Recently**
   - Database might have old Round 1 value
   - Need to run sync to get latest from API

## How to Debug

### 1. Check Raw API Response

Use the new diagnostic endpoint:

```bash
curl https://masters-production.up.railway.app/api/validation/api-raw | jq
```

This shows:
- What `currentRound` value the API returned
- What type it is (string, int, dict, etc.)
- Full API response for inspection

### 2. Check Database Value

```bash
curl https://masters-production.up.railway.app/api/tournament/current | jq '.current_round'
```

### 3. Check Sync Logs

Look for log messages like:
```
API returned currentRound: 2 (type: <class 'int'>)
Parsed current_round: 2
Updated tournament: The American Express (2026) - Round 2
```

### 4. Manual API Check

You can also check the Slash Golf API directly (if you have access):
- Call `/tournament` endpoint
- Look for `currentRound` field
- See what value it returns

## Alternative: Date-Based Calculation

If the API doesn't reliably provide `currentRound`, we could calculate it from dates:

```python
def calculate_round_from_date(tournament: Tournament) -> int:
    """Calculate current round based on tournament dates."""
    today = date.today()
    
    # Round 1: Start date
    # Round 2: Start date + 1 day
    # Round 3: Start date + 2 days
    # Round 4: Start date + 3 days
    
    if today < tournament.start_date:
        return 0  # Not started
    elif today == tournament.start_date:
        return 1
    elif today == tournament.start_date + timedelta(days=1):
        return 2
    elif today == tournament.start_date + timedelta(days=2):
        return 3
    elif today >= tournament.start_date + timedelta(days=3):
        return 4
    else:
        return 1  # Default
```

**However**, this is less reliable because:
- Tournaments can have delays
- Rounds might finish early/late
- API knows the actual round status

## Recommendation

1. **First**: Check what the API is actually returning using `/api/validation/api-raw`
2. **If API returns Round 1**: The tournament might actually still be in Round 1, or API hasn't updated
3. **If API returns Round 2 but database shows Round 1**: There's a parsing issue
4. **If API doesn't return currentRound**: We might need date-based fallback

## Next Steps

1. Run sync and check logs for `API returned currentRound: ...`
2. Check `/api/validation/api-raw` to see raw API data
3. Compare API value vs database value
4. If mismatch, we can add date-based fallback logic

---

*Last Updated: January 2026*
