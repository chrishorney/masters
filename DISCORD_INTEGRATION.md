# Discord Integration Implementation

## Overview

Discord integration has been implemented to send real-time notifications for exciting tournament events. The integration is **completely optional** and will not break production if Discord is disabled.

## Features Implemented

### 1. Bonus Point Notifications
- **Hole-in-One**: "🎯 HOLE-IN-ONE! Player X just got a hole-in-one on hole Y!"
- **Double Eagle (Albatross)**: "🦅 DOUBLE EAGLE! Player X got a double eagle on hole Y!"
- **Eagle**: "🦅 EAGLE! Player X got an eagle on hole Y!"

### 2. Position Change Notifications
- **New Leader**: "👑 NEW LEADER! Entry X has taken the lead!"
- **Big Position Changes**: "📈 Big Move Up/Down! Entry X moved from #Y to #Z!"

## Configuration

### Environment Variables

Add these to your `.env` file (or Railway/Vercel environment variables):

```bash
# Discord Integration (optional)
DISCORD_ENABLED=false
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1464311605084028931/qPXmTCWouXiB6Ahz6wIZWCJhV0OwlArZh-Qqoaibi8OEow_uS_9bAP-Pgz2atpGnfFHz
```

### Setting Up Discord Webhook

1. **Create Discord Server** (or use existing)
2. **Choose Channel** for notifications (e.g., `#announcements`, `#tournament-updates`)
   - **Important**: Each webhook is tied to a specific channel
   - To change channels, create a new webhook for the desired channel
3. **Create Webhook**:
   - Go to the channel where you want notifications
   - Click the gear icon (⚙️) next to the channel name → "Integrations"
   - OR go to Server Settings → Integrations → Webhooks
   - Click "New Webhook" or "Create Webhook"
   - Name it (e.g., "Tournament Bot")
   - **Select the channel** you want (e.g., `#announcements`)
   - Click "Copy Webhook URL"
4. **Add to Environment** (Railway/Vercel):
   ```bash
   DISCORD_ENABLED=true
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
   ```
5. **Update in Railway**:
   - Go to your Railway project → Variables
   - Update `DISCORD_WEBHOOK_URL` with the new webhook URL
   - Railway will automatically redeploy

## How It Works

### Fire-and-Forget Pattern

Discord notifications use a **fire-and-forget** pattern:
- Notifications are sent asynchronously in the background
- If Discord is down or fails, scoring continues normally
- Errors are logged but don't affect tournament scoring
- No blocking - scoring happens immediately

### Integration Points

1. **Bonus Points** (`backend/app/services/scoring.py`):
   - When a bonus point is created (hole-in-one, eagle, etc.)
   - Notification is sent automatically
   - Only for special bonuses (not GIR/fairways)

2. **Position Changes** (`backend/app/services/score_calculator.py`):
   - After ranking snapshots are created
   - Checks for new leader
   - Checks for big position changes (5+ positions)

## Safety Features

### Production-Safe

- ✅ **Optional**: Disabled by default (`DISCORD_ENABLED=false`)
- ✅ **Non-Blocking**: Uses fire-and-forget async tasks
- ✅ **Error Handling**: All errors are caught and logged
- ✅ **Graceful Degradation**: If Discord fails, scoring continues
- ✅ **No Breaking Changes**: Existing functionality unchanged

### Testing Without Discord

The application works perfectly without Discord:
- Set `DISCORD_ENABLED=false` (or leave unset)
- All scoring and calculations work normally
- No errors or warnings (Discord service is silently disabled)

## Notification Examples

### Hole-in-One
```
🎯 HOLE-IN-ONE!
Scheffler just got a hole-in-one on hole 7!

Player: Scheffler
Hole: 7
Round: Round 2
Tournament: The Masters

All entries with this player earned 3 bonus points!
```

### New Leader
```
👑 NEW LEADER!
Entry "John's Team" has taken the lead!

New Leader: John's Team
Total Points: 45.0
Round: Round 2
Previous Leader: Jane's Team
```

### Big Position Change
```
📈 Big Move Up!
Entry "Mike's Picks" moved from #15 to #3!

Entry: Mike's Picks
Position Change: #15 → #3
Total Points: 38.5
Round: Round 2
```

## Files Modified

1. **`backend/app/services/discord.py`** (NEW)
   - Discord service with webhook support
   - Notification methods for all event types

2. **`backend/app/config.py`**
   - Added `discord_webhook_url` and `discord_enabled` settings

3. **`backend/app/services/scoring.py`**
   - Integrated Discord notifications for bonus points
   - Fire-and-forget async pattern

4. **`backend/app/services/score_calculator.py`**
   - Integrated Discord notifications for position changes
   - New leader detection
   - Big position change detection

5. **`backend/env.template`**
   - Added Discord configuration variables

## Testing

### Test Locally

1. **Without Discord** (default):
   ```bash
   # Don't set DISCORD_ENABLED or set it to false
   # Run scoring - should work normally
   ```

2. **With Discord**:
   ```bash
   # Set DISCORD_ENABLED=true and DISCORD_WEBHOOK_URL
   # Trigger a bonus point (e.g., hole-in-one)
   # Check Discord channel for notification
   ```

### Test in Production

1. **Add Environment Variables** to Railway:
   - `DISCORD_ENABLED=true`
   - `DISCORD_WEBHOOK_URL=your_webhook_url`

2. **Restart Service** (Railway will auto-restart)

3. **Monitor Logs**:
   - Check for "Discord service enabled" message
   - Watch for notification errors (non-critical)

## Troubleshooting

### Notifications Not Sending

1. **Check Configuration**:
   - `DISCORD_ENABLED=true`?
   - `DISCORD_WEBHOOK_URL` set correctly?
   - Webhook URL is valid?

2. **Check Logs**:
   - Look for "Discord service enabled" on startup
   - Check for "Discord notification failed" warnings

3. **Test Webhook**:
   ```bash
   curl -X POST "YOUR_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"embeds":[{"title":"Test","description":"Testing webhook"}]}'
   ```

### Rate Limiting

Discord webhooks have a rate limit of **30 requests per minute**. If you see rate limit errors:
- Notifications will be logged but not sent
- Scoring continues normally
- Consider batching notifications (future enhancement)

## Future Enhancements

- Round completion notifications
- Tournament start/end notifications
- Configurable notification preferences
- Multiple webhooks for different channels
- Notification batching to avoid rate limits

## Notes

- All Discord operations are **non-blocking** and **non-critical**
- Scoring will work perfectly even if Discord is completely down
- No database changes required
- No API changes required
- Backwards compatible with existing deployments
