# SmartSheet Import Format

This document describes the expected format for SmartSheet exports that will be imported into the application.

## Entries Import Format

### Required Columns

The SmartSheet export for entries should have the following columns:

| Column Name | Description | Example |
|------------|-------------|---------|
| Participant Name | Name of the person entering the pool | John Smith |
| Player 1 Name | First selected golfer | Tiger Woods |
| Player 2 Name | Second selected golfer | Phil Mickelson |
| Player 3 Name | Third selected golfer | Rory McIlroy |
| Player 4 Name | Fourth selected golfer | Jordan Spieth |
| Player 5 Name | Fifth selected golfer | Dustin Johnson |
| Player 6 Name | Sixth selected golfer | Brooks Koepka |

### Example CSV Format

```csv
Participant Name,Player 1 Name,Player 2 Name,Player 3 Name,Player 4 Name,Player 5 Name,Player 6 Name
John Smith,Tiger Woods,Phil Mickelson,Rory McIlroy,Jordan Spieth,Dustin Johnson,Brooks Koepka
Jane Doe,Scottie Scheffler,Jon Rahm,Collin Morikawa,Xander Schauffele,Patrick Cantlay,Viktor Hovland
```

### Notes

- Player names should match the names used in the Slash Golf API
- The system will attempt to match player names to playerIds
- If a player cannot be matched, the import will report an error
- Participant names can be duplicated (multiple entries per person)

## Rebuys Import Format

### Required Columns

The SmartSheet export for rebuys should have the following columns:

| Column Name | Description | Example |
|------------|-------------|---------|
| Participant Name | Name of the person making the rebuy | John Smith |
| Original Player Name | Name of the player being replaced | Tiger Woods |
| Rebuy Player Name | Name of the replacement player | Scottie Scheffler |
| Rebuy Type | Type of rebuy: "missed_cut" or "underperformer" | missed_cut |

### Example CSV Format

```csv
Participant Name,Original Player Name,Rebuy Player Name,Rebuy Type
John Smith,Tiger Woods,Scottie Scheffler,missed_cut
Jane Doe,Phil Mickelson,Jon Rahm,underperformer
```

### Rebuy Types

1. **missed_cut**: Player did not make the cut
   - Original player's Thursday/Friday points remain
   - Rebuy player earns points from Saturday/Sunday only
   - Weekend bonus still eligible

2. **underperformer**: Player made cut but is underperforming
   - Original player's Thursday/Friday points remain
   - Weekend bonus (5 points) is FORFEITED
   - Rebuy player earns points from Saturday/Sunday only

### Notes

- Participant name must match an existing entry
- Original player name must match a player in that participant's entry
- Rebuy player name must match a valid player in the tournament
- Rebuy type must be exactly "missed_cut" or "underperformer"
- Multiple rebuys per participant are allowed

## Import Process

1. **Export from SmartSheet**
   - Export as CSV or Excel format
   - Ensure column names match exactly (case-sensitive)

2. **Upload via Admin Interface**
   - Log in as admin
   - Navigate to Import section
   - Select file type (Entries or Rebuys)
   - Upload file

3. **Validation**
   - System validates column names
   - System validates data format
   - System attempts to match player names
   - Errors are reported with details

4. **Processing**
   - Valid entries are created in database
   - Player names are matched to playerIds
   - Rebuys are linked to existing entries
   - Success/error report is displayed

## Error Handling

### Common Errors

1. **Column Name Mismatch**
   - Error: "Column 'Player 1' not found. Expected 'Player 1 Name'"
   - Solution: Check column names match exactly

2. **Player Not Found**
   - Error: "Player 'Tiger Woods' not found in tournament"
   - Solution: Verify player name matches API data

3. **Participant Not Found (Rebuys)**
   - Error: "Participant 'John Smith' not found"
   - Solution: Ensure entries are imported before rebuys

4. **Invalid Rebuy Type**
   - Error: "Invalid rebuy type 'missedcut'. Must be 'missed_cut' or 'underperformer'"
   - Solution: Check rebuy type spelling

## Best Practices

1. **Before Import**
   - Verify column names match exactly
   - Check player name spelling
   - Ensure all required columns are present
   - Test with a small sample first

2. **After Import**
   - Review error report
   - Verify entries in leaderboard
   - Check rebuy assignments
   - Confirm player assignments

3. **Data Quality**
   - Use consistent player name format
   - Avoid special characters in names
   - Keep participant names consistent
   - Double-check rebuy types

## Example Files

Example CSV files will be provided in the `docs/examples/` directory once the import functionality is implemented.
