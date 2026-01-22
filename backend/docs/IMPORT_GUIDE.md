# SmartSheet Import Guide

This guide explains how to import participant entries and rebuys from SmartSheet exports.

## Overview

The import system accepts CSV files exported from SmartSheet and automatically:
- Creates participants
- Matches player names to player IDs
- Creates entries with 6 players each
- Processes rebuys and links them to entries
- Validates all data and reports errors

## Import Endpoints

### Import Entries

**Endpoint:** `POST /api/admin/import/entries`

**Parameters:**
- `tournament_id` (form field): Tournament ID to import entries for
- `file` (file upload): CSV file with entries

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/admin/import/entries" \
  -F "tournament_id=1" \
  -F "file=@entries.csv"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/api/admin/import/entries"
files = {"file": open("entries.csv", "rb")}
data = {"tournament_id": 1}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Import Rebuys

**Endpoint:** `POST /api/admin/import/rebuys`

**Parameters:**
- `tournament_id` (form field): Tournament ID
- `file` (file upload): CSV file with rebuys

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/admin/import/rebuys" \
  -F "tournament_id=1" \
  -F "file=@rebuys.csv"
```

### Preview Players

**Endpoint:** `GET /api/admin/import/preview?tournament_id=1&limit=10`

Use this to see available players in a tournament before importing. This helps verify player name matching.

## CSV Format

### Entries Format

**Required Columns:**
- `Participant Name` - Name of the person entering the pool
- `Player 1 Name` - First selected golfer
- `Player 2 Name` - Second selected golfer
- `Player 3 Name` - Third selected golfer
- `Player 4 Name` - Fourth selected golfer
- `Player 5 Name` - Fifth selected golfer
- `Player 6 Name` - Sixth selected golfer

**Example:**
```csv
Participant Name,Player 1 Name,Player 2 Name,Player 3 Name,Player 4 Name,Player 5 Name,Player 6 Name
John Smith,Collin Morikawa,Sam Burns,Peter Malnati,Cameron Young,Xander Schauffele,Patrick Cantlay
Jane Doe,Scottie Scheffler,Jon Rahm,Viktor Hovland,Jordan Spieth,Dustin Johnson,Brooks Koepka
```

### Rebuys Format

**Required Columns:**
- `Participant Name` - Name of the person making the rebuy
- `Original Player Name` - Name of the player being replaced
- `Rebuy Player Name` - Name of the replacement player
- `Rebuy Type` - Either `missed_cut` or `underperformer`

**Example:**
```csv
Participant Name,Original Player Name,Rebuy Player Name,Rebuy Type
John Smith,Collin Morikawa,Scottie Scheffler,missed_cut
Jane Doe,Sam Burns,Jon Rahm,underperformer
```

## Player Name Matching

The system matches player names using several strategies:

1. **Exact Match**: Matches full name exactly (case-insensitive)
2. **First/Last Name Split**: Matches first and last name separately
3. **Tournament Leaderboard**: Searches in the tournament's current leaderboard

**Tips for successful matching:**
- Use full names (e.g., "Collin Morikawa" not "C. Morikawa")
- Match the format used in the API (usually "FirstName LastName")
- Check the preview endpoint to see exact player names
- Avoid nicknames or abbreviations

## Response Format

### Success Response

```json
{
  "success": true,
  "imported": 25,
  "skipped": 2,
  "errors": [
    {
      "row": 5,
      "participant": "John Smith",
      "error": "Player 3 'Unknown Player' not found"
    }
  ]
}
```

### Error Response

```json
{
  "success": false,
  "error": "Missing required columns: Player 1 Name, Player 2 Name"
}
```

## Error Handling

### Common Errors

1. **Missing Columns**
   - Error: "Missing required columns: Player 1 Name"
   - Solution: Ensure column names match exactly (case-sensitive)

2. **Player Not Found**
   - Error: "Player 3 'Unknown Player' not found"
   - Solution: Check player name spelling, use preview endpoint to verify

3. **Participant Not Found (Rebuys)**
   - Error: "Participant 'John Smith' not found"
   - Solution: Import entries before importing rebuys

4. **Invalid Rebuy Type**
   - Error: "Invalid rebuy type 'missedcut'"
   - Solution: Use exactly "missed_cut" or "underperformer"

5. **Duplicate Entry**
   - Entry is skipped if exact duplicate exists (same participant, tournament, and players)

## Workflow

### Step 1: Prepare Your Data

1. Export from SmartSheet as CSV
2. Verify column names match exactly
3. Check player name formatting
4. Save file

### Step 2: Preview Players (Optional)

```bash
curl "http://localhost:8000/api/admin/import/preview?tournament_id=1&limit=20"
```

This shows you the exact player names in the tournament.

### Step 3: Import Entries

```bash
curl -X POST "http://localhost:8000/api/admin/import/entries" \
  -F "tournament_id=1" \
  -F "file=@entries.csv"
```

Review the response for any errors.

### Step 4: Import Rebuys (After Cut)

```bash
curl -X POST "http://localhost:8000/api/admin/import/rebuys" \
  -F "tournament_id=1" \
  -F "file=@rebuys.csv"
```

### Step 5: Verify

Check the leaderboard or entries endpoint to verify imports were successful.

## Using the API Documentation

The easiest way to use these endpoints is through the interactive API documentation:

1. Start the backend server: `uvicorn app.main:app --reload`
2. Visit: `http://localhost:8000/docs`
3. Navigate to the "admin" section
4. Find the import endpoints
5. Use the "Try it out" feature to upload files

## Best Practices

1. **Test with Small Files First**
   - Import a few entries first to verify format
   - Check for errors before importing full dataset

2. **Verify Player Names**
   - Use the preview endpoint to see exact player names
   - Match names exactly as they appear in the tournament

3. **Import Order**
   - Always import entries before rebuys
   - Rebuys require existing entries

4. **Error Review**
   - Always review the errors array in the response
   - Fix errors and re-import if needed

5. **Backup**
   - Keep original SmartSheet exports
   - Export database before large imports

## Example Files

Example CSV files are available in `docs/examples/`:
- `entries_example.csv` - Example entries format
- `rebuys_example.csv` - Example rebuys format

## Troubleshooting

### Player Names Not Matching

1. Check the preview endpoint for exact names
2. Try different name formats (full name vs first/last)
3. Verify player is in the tournament

### Import Fails Silently

1. Check the response for errors array
2. Verify file encoding (should be UTF-8)
3. Check file format (must be CSV)

### Duplicate Entries

- Duplicate entries (same participant, tournament, players) are automatically skipped
- This is expected behavior to prevent duplicates
