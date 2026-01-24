# Discord Notifications Reference

Complete guide to all Discord notifications, when they're sent, and where they're configured.

## Overview

Discord notifications are sent automatically when specific events occur during a tournament. All notifications use a **fire-and-forget** pattern, meaning they're sent asynchronously and won't block or break scoring if Discord fails.

## Configuration

**Location**: `backend/app/config.py` and Railway environment variables

```python
discord_webhook_url: str = "https://discord.com/api/webhooks/..."
discord_enabled: bool = False  # Set to True to enable
```

**Environment Variables**:
- `DISCORD_ENABLED=true` (required to enable)
- `DISCORD_WEBHOOK_URL=your_webhook_url` (required)

---

## Notification Types & Triggers

### 1. 🎯 Hole-in-One Notification

**When Sent**: When a player gets a hole-in-one (detected during score calculation)

**Trigger Location**: `backend/app/services/scoring.py`
- **Method**: `_notify_discord_bonus()` (line 536)
- **Called From**: `calculate_and_save_daily_score()` (line 472, 527)
- **Condition**: Bonus type is `"hole_in_one"` and bonus points are calculated

**Notification Details**:
- **Title**: "🎯 HOLE-IN-ONE!"
- **Color**: Red (0xff0000)
- **Includes**: Player name, hole number, round, tournament name
- **Footer**: "All entries with this player earned 3 bonus points!"

**Code Flow**:
```
Score calculation → Bonus point detected → _notify_discord_bonus_async() → 
DiscordService.notify_hole_in_one()
```

---

### 2. 🦅 Eagle Notification

**When Sent**: When a player gets an eagle (detected during score calculation)

**Trigger Location**: `backend/app/services/scoring.py`
- **Method**: `_notify_discord_bonus()` (line 536)
- **Called From**: `calculate_and_save_daily_score()` (line 472, 527)
- **Condition**: Bonus type is `"eagle"` and bonus points are calculated

**Notification Details**:
- **Title**: "🦅 EAGLE!"
- **Color**: Gold/Orange (0xffaa00)
- **Includes**: Player name, hole number, round, tournament name
- **Footer**: "All entries with this player earned 2 bonus points!"

**Code Flow**:
```
Score calculation → Bonus point detected → _notify_discord_bonus_async() → 
DiscordService.notify_eagle()
```

---

### 3. 🦅 Double Eagle (Albatross) Notification

**When Sent**: When a player gets a double eagle/albatross (detected during score calculation)

**Trigger Location**: `backend/app/services/scoring.py`
- **Method**: `_notify_discord_bonus()` (line 536)
- **Called From**: `calculate_and_save_daily_score()` (line 472, 527)
- **Condition**: Bonus type is `"double_eagle"` and bonus points are calculated

**Notification Details**:
- **Title**: "🦅 DOUBLE EAGLE (ALBATROSS)!"
- **Color**: Orange (0xff6600)
- **Includes**: Player name, hole number, round, tournament name
- **Footer**: "All entries with this player earned 3 bonus points!"

**Code Flow**:
```
Score calculation → Bonus point detected → _notify_discord_bonus_async() → 
DiscordService.notify_double_eagle()
```

---

### 4. 👑 New Leader Notification

**When Sent**: When a different entry takes the lead (detected after ranking snapshot)

**Trigger Location**: `backend/app/services/score_calculator.py`
- **Method**: `_notify_discord_position_changes()` (line 297)
- **Called From**: `_capture_ranking_snapshot()` (line 127)
- **Condition**: 
  - Current leader is different from previous leader
  - OR first snapshot for a round (no previous leader)

**Notification Details**:
- **Title**: "👑 NEW LEADER!"
- **Color**: Gold (0xffd700)
- **Includes**: New leader name, total points, round, previous leader (if applicable), tournament name

**Code Flow**:
```
Score calculation → Ranking snapshot created → _notify_discord_position_changes_async() → 
Check for leader change → DiscordService.notify_new_leader()
```

**Frequency**: Sent every time the leader changes (could be multiple times per sync if leader changes frequently)

---

### 5. 📈 Big Position Change Notification

**When Sent**: When an entry moves 5 or more positions up or down (detected after ranking snapshot)

**Trigger Location**: `backend/app/services/score_calculator.py`
- **Method**: `_notify_discord_position_changes()` (line 297)
- **Called From**: `_capture_ranking_snapshot()` (line 127)
- **Condition**: 
  - Entry moved 5+ positions from previous snapshot
  - Compares current position to previous position

**Notification Details**:
- **Title**: "📈 Big Move Up!" or "📈 Big Move Down!"
- **Color**: Green (0x00ff00) for up, Orange (0xff6600) for down
- **Includes**: Entry name, old position, new position, total points, round

**Code Flow**:
```
Score calculation → Ranking snapshot created → _notify_discord_position_changes_async() → 
Check all entries for 5+ position changes → DiscordService.notify_big_position_change()
```

**Frequency**: Sent for each entry that moves 5+ positions (could be multiple per sync)

---

### 6. 🏁 Round Complete Notification

**When Sent**: When a round completes (detected when `current_round` increases)

**Trigger Location**: `backend/app/services/data_sync.py`
- **Method**: `_notify_discord_round_complete_async()` (line 634)
- **Called From**: `sync_tournament()` (line 216)
- **Condition**: 
  - Tournament exists
  - `current_round` increased (e.g., Round 1 → Round 2)
  - Previous round was at least Round 1

**Notification Details**:
- **Title**: "🏁 Round {N} Complete!"
- **Color**: Blue (0x0099ff)
- **Includes**: Completed round number, current leader name, leader points, total entries, tournament name

**Code Flow**:
```
Tournament sync → API returns new current_round → Compare to old current_round → 
If increased → _notify_discord_round_complete_async() → DiscordService.notify_round_complete()
```

**Frequency**: Sent once per round completion (typically 4 times per tournament)

---

### 7. 🏌️ Tournament Start Notification

**When Sent**: When entries are first imported for a tournament (first time entries are added)

**Trigger Location**: `backend/app/api/admin/imports.py`
- **Method**: `import_entries()` endpoint (line 12)
- **Condition**: 
  - First import for tournament (no existing entries before import)
  - At least one entry was successfully imported

**Notification Details**:
- **Title**: "🏌️ Tournament Started!"
- **Color**: Green (0x00ff00)
- **Includes**: Tournament name, year, total entry count

**Code Flow**:
```
Entry import → Check if first import → If yes and entries imported → 
Notify tournament start → DiscordService.notify_tournament_start()
```

**Frequency**: Sent once per tournament (only on first entry import)

---

## Notification Timing Summary

| Notification | When Sent | Frequency | Trigger |
|-------------|-----------|-----------|---------|
| 🎯 Hole-in-One | During score calculation | As it happens | Bonus point created |
| 🦅 Eagle | During score calculation | As it happens | Bonus point created |
| 🦅 Double Eagle | During score calculation | As it happens | Bonus point created |
| 👑 New Leader | After ranking snapshot | Every leader change | Position snapshot |
| 📈 Big Move | After ranking snapshot | Per entry (5+ move) | Position snapshot |
| 🏁 Round Complete | During tournament sync | Once per round | Round number increases |
| 🏌️ Tournament Start | Entry import | Once per tournament | First entry import |

---

## Code Locations

### Service Files

1. **`backend/app/services/discord.py`**
   - Main Discord service with all notification methods
   - `notify_hole_in_one()`, `notify_eagle()`, `notify_double_eagle()`
   - `notify_new_leader()`, `notify_big_position_change()`
   - `notify_round_complete()`, `notify_tournament_start()`

2. **`backend/app/services/scoring.py`**
   - Bonus point notifications (lines 472, 527, 536-589)
   - Triggers: Hole-in-one, Eagle, Double Eagle

3. **`backend/app/services/score_calculator.py`**
   - Position change notifications (lines 127, 269-401)
   - Triggers: New Leader, Big Position Changes

4. **`backend/app/services/data_sync.py`**
   - Round completion notification (lines 216, 634-699)
   - Trigger: Round number increases

5. **`backend/app/api/admin/imports.py`**
   - Tournament start notification (lines 59-82)
   - Trigger: First entry import

### Test Endpoint

**`backend/app/api/admin/discord.py`**
- Test endpoint for all notification types
- `POST /api/admin/discord/test?notification_type={type}&tournament_id={id}`
- Available types: `hole_in_one`, `eagle`, `double_eagle`, `new_leader`, `big_move`, `round_complete`, `tournament_start`

---

## How Notifications Are Sent

### Fire-and-Forget Pattern

All notifications use asynchronous fire-and-forget:
- Sent in background (non-blocking)
- Errors are logged but don't affect scoring
- Uses `asyncio.create_task()` for async execution

### Example Flow

```python
# In scoring.py
self._notify_discord_bonus_async(bonus, round_id, tournament)

# Which calls:
async def _notify_discord_bonus(...):
    # Fire-and-forget
    asyncio.create_task(notify())
    
    # Or in sync context:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(notify())
    else:
        loop.run_until_complete(notify())
```

---

## Disabling Notifications

### Disable All Notifications

Set in Railway environment variables:
```bash
DISCORD_ENABLED=false
```

Or remove `DISCORD_WEBHOOK_URL`.

### Disable Specific Notification Types

Currently, all notification types are enabled together. To disable specific types, you would need to modify the code in:
- `backend/app/services/scoring.py` (bonus notifications)
- `backend/app/services/score_calculator.py` (position notifications)
- `backend/app/services/data_sync.py` (round completion)
- `backend/app/api/admin/imports.py` (tournament start)

---

## Rate Limiting

**Discord Webhook Limits**:
- 30 requests per minute per webhook
- If exceeded, notifications will fail silently (logged but not sent)

**Current Implementation**:
- No batching or rate limit handling
- Each notification is sent immediately
- If many events occur quickly, some may be rate-limited

**Future Enhancement**: Add notification queuing and batching to respect rate limits.

---

## Testing

### Test from Admin UI

1. Go to `/admin` → Tournament Management tab
2. Scroll to "Discord Integration" section
3. Click "Check Discord Status" to verify enabled
4. Click any test button to send test notification

### Test via API

```bash
# Check status
curl https://masters-production.up.railway.app/api/admin/discord/status

# Test hole-in-one
curl -X POST "https://masters-production.up.railway.app/api/admin/discord/test?notification_type=hole_in_one&tournament_id=2"

# Test new leader
curl -X POST "https://masters-production.up.railway.app/api/admin/discord/test?notification_type=new_leader&tournament_id=2"
```

---

## Troubleshooting

### Notifications Not Sending

1. **Check Discord Status**:
   ```bash
   curl https://masters-production.up.railway.app/api/admin/discord/status
   ```
   Should return `{"enabled": true, ...}`

2. **Check Railway Logs**:
   - Look for "Discord service enabled" on startup
   - Check for "Discord notification failed" warnings

3. **Verify Webhook URL**:
   - Test webhook URL directly:
   ```bash
   curl -X POST "YOUR_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"embeds":[{"title":"Test","description":"Testing webhook"}]}'
   ```

4. **Check Event Triggers**:
   - Ensure events are actually occurring (e.g., bonus points being calculated)
   - Check that scoring/sync is running

### Too Many Notifications

- Reduce sync frequency (increase interval)
- Modify thresholds (e.g., require 10+ position change instead of 5)
- Disable specific notification types in code

---

## Summary

All Discord notifications are configured in:
- **Service**: `backend/app/services/discord.py` (notification methods)
- **Triggers**: Various service files (scoring, score_calculator, data_sync, imports)
- **Config**: `backend/app/config.py` and Railway environment variables
- **Test**: `backend/app/api/admin/discord.py` and admin UI

Notifications are sent automatically when events occur, using a fire-and-forget pattern that won't affect tournament scoring if Discord fails.
