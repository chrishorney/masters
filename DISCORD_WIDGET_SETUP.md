# Discord Widget Setup Guide

## Problem: Widget Shows Loading Screen Forever

If the Discord widget is stuck on a loading screen, follow these steps:

## Step 1: Enable Server Widget in Discord

1. **Open Discord** and go to your server
2. Click **Server Settings** (gear icon next to server name)
3. Go to **Widget** (in the left sidebar)
4. **Enable Server Widget** (toggle it ON)
5. **Copy the Server ID** (long number shown on this page)
6. Optionally customize:
   - **Invite Channel** - Which channel users join when clicking widget
   - **Widget Style** - Light or Dark theme

## Step 2: Set Server ID in Railway

1. Go to **Railway Dashboard** → Your Service → **Variables**
2. Add or update: `DISCORD_SERVER_ID=your_server_id_here`
   - The Server ID is a long number (e.g., `123456789012345678`)
   - **Important:** This is NOT the same as the invite code
3. **Restart** the Railway service

## Step 3: Verify Widget URL

Test the widget URL directly:
```bash
curl https://your-railway-app.up.railway.app/api/discord/widget
```

Should return:
```json
{
  "server_id": "123456789012345678",
  "widget_url": "https://discord.com/widget?id=123456789012345678&theme=dark"
}
```

## Step 4: Test Widget URL in Browser

Open the widget URL directly in your browser:
```
https://discord.com/widget?id=YOUR_SERVER_ID&theme=dark
```

**If this doesn't work:**
- Widget is not enabled in Discord
- Server ID is incorrect
- Server might have restrictions

## Step 5: Check Browser Console

1. Open your leaderboard page
2. Press **F12** to open Developer Tools
3. Go to **Console** tab
4. Look for errors related to:
   - CORS (Cross-Origin Resource Sharing)
   - iframe loading
   - Network errors

## Common Issues

### Issue: "Widget not configured"
**Solution:** Set `DISCORD_SERVER_ID` in Railway environment variables

### Issue: Widget loads but shows "Server Widget is Disabled"
**Solution:** Enable Server Widget in Discord (Server Settings → Widget)

### Issue: Widget stuck on loading screen
**Possible causes:**
1. **Widget not enabled** - Enable it in Discord server settings
2. **Wrong Server ID** - Verify the ID matches your Discord server
3. **Server restrictions** - Some servers have widget disabled for privacy
4. **Browser blocking** - Try a different browser or disable ad blockers

### Issue: "Failed to load Discord widget"
**Solution:**
- Check that Server Widget is enabled in Discord
- Verify Server ID is correct (no extra spaces or characters)
- Make sure the server allows widgets

## How to Get Server ID

### Method 1: From Widget Settings
1. Discord → Server Settings → Widget
2. Server ID is shown at the top of the page

### Method 2: Developer Mode
1. Discord → User Settings → Advanced
2. Enable **Developer Mode**
3. Right-click your server name → **Copy Server ID**

## Widget Features

The Discord widget shows:
- ✅ Server name and icon
- ✅ Online member count
- ✅ List of online members
- ✅ Join button (if not already a member)
- ❌ **Does NOT show** channel messages (Discord doesn't allow this)

## Alternative: Use Discord Invite Link

If the widget doesn't work, you can use the invite link instead:
- Set `DISCORD_INVITE_URL` in Railway
- The invite button will appear on homepage and leaderboard
- Users can click to join and see updates

## Verification Checklist

- [ ] Server Widget enabled in Discord (Server Settings → Widget)
- [ ] Server ID copied correctly (long number)
- [ ] `DISCORD_SERVER_ID` set in Railway
- [ ] Railway service restarted after setting variable
- [ ] Widget URL works when opened directly in browser
- [ ] No browser console errors
- [ ] Widget appears on leaderboard page

## Still Not Working?

1. **Check Railway logs** for errors
2. **Test the API endpoint** directly:
   ```bash
   curl https://your-app.railway.app/api/discord/widget
   ```
3. **Verify Server ID** matches exactly (no spaces, correct format)
4. **Try different browser** (Chrome, Firefox, Safari)
5. **Disable browser extensions** that might block iframes
6. **Check Discord server settings** - some servers disable widgets for privacy
