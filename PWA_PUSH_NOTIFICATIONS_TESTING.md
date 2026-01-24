# Testing Push Notifications

This guide will help you test the push notification system end-to-end.

## Prerequisites

Before testing, ensure you have:

1. ✅ **VAPID Keys Generated** - Run `python3 backend/generate_vapid_keys.py`
2. ✅ **Environment Variables Set in Railway**:
   - `VAPID_PUBLIC_KEY` = (your public key hex string)
   - `VAPID_PRIVATE_KEY` = (your private key hex string)
   - `VAPID_EMAIL` = `mailto:your-email@example.com`
   - `PUSH_NOTIFICATIONS_ENABLED` = `true`
3. ✅ **Database Migration Run** - `alembic upgrade head`
4. ✅ **Backend Deployed** - Railway should have deployed with the new code
5. ✅ **Frontend Deployed** - Vercel should have deployed successfully

## Step 1: Verify Backend Configuration

### 1.1 Check Push Service Status

```bash
curl https://masters-production.up.railway.app/api/push/status
```

**Expected Response:**
```json
{
  "enabled": true,
  "vapid_configured": true,
  "status": "enabled"
}
```

If `enabled: false`, check:
- `PUSH_NOTIFICATIONS_ENABLED=true` in Railway
- VAPID keys are set correctly
- Backend has been redeployed after adding environment variables

### 1.2 Get VAPID Public Key

```bash
curl https://masters-production.up.railway.app/api/push/public-key
```

**Expected Response:**
```json
{
  "publicKey": "04e38f9fd104be2717b6557aad29e2fce55121270cdb7540e9bd6ab2d078316805d09256c826eedc7404f42e1eae4c2996a796ca263afef09981370f1a44547596"
}
```

If you get a 503 error, push notifications are not enabled.

## Step 2: Test Frontend Subscription

### 2.1 Open the Website

1. Go to your deployed website (Vercel URL)
2. Navigate to the homepage
3. Scroll down to the "Push Notifications" section

### 2.2 Subscribe to Notifications

1. Click the **"Enable Notifications"** button
2. Your browser will prompt you to allow notifications
3. Click **"Allow"** in the browser prompt
4. You should see a success message: "✓ You're subscribed to push notifications"

### 2.3 Verify Subscription in Database

Check that your subscription was saved:

```bash
# Connect to your database and run:
SELECT id, endpoint, active, created_at 
FROM push_subscriptions 
WHERE active = true;
```

You should see at least one row with your subscription.

## Step 3: Test Push Notifications

### 3.1 Test via Admin Endpoint (Recommended)

I'll create a test endpoint that sends a test notification to all subscribers:

```bash
curl -X POST "https://masters-production.up.railway.app/api/admin/push/test?message=Test%20notification"
```

**Expected Response:**
```json
{
  "success": true,
  "sent_count": 1,
  "message": "Test notification sent to 1 subscribers"
}
```

### 3.2 Test via Real Tournament Events

Push notifications are automatically sent for:
- **Hole-in-One**: When a player gets a hole-in-one
- **Eagle**: When a player gets an eagle
- **Double Eagle**: When a player gets a double eagle
- **New Leader**: When an entry takes the lead
- **Big Position Change**: When an entry moves 5+ positions
- **Round Complete**: When a round finishes
- **Tournament Start**: When entries are first imported

To test with real events:
1. Wait for a tournament event to occur
2. Or manually trigger scoring/sync operations that would create these events

### 3.3 Test via Discord Test Endpoint (Alternative)

If you have Discord notifications enabled, you can use the existing Discord test endpoint, which will also trigger push notifications:

```bash
curl -X POST "https://masters-production.up.railway.app/api/admin/discord/test?tournament_id=2&notification_type=hole_in_one"
```

## Step 4: Verify Notification Delivery

### 4.1 Check Browser Console

1. Open browser DevTools (F12)
2. Go to the Console tab
3. Look for any errors related to push notifications
4. You should see: `"Subscribed to push notifications"` when subscribing

### 4.2 Check Service Worker

1. Open browser DevTools (F12)
2. Go to the Application tab (Chrome) or Storage tab (Firefox)
3. Click on "Service Workers"
4. Verify your service worker is active and running
5. Check for any errors

### 4.3 Check Notification Settings

1. **Chrome/Edge**: 
   - Go to `chrome://settings/content/notifications`
   - Verify your site is allowed

2. **Firefox**:
   - Go to `about:preferences#privacy`
   - Click "Permissions" → "Notifications"
   - Verify your site is allowed

3. **Safari** (iOS):
   - Settings → Safari → Notifications
   - Verify your site is allowed

## Step 5: Troubleshooting

### Issue: "Push notifications are not enabled"

**Solution:**
1. Check Railway environment variables
2. Ensure `PUSH_NOTIFICATIONS_ENABLED=true`
3. Redeploy backend after setting environment variables

### Issue: "Failed to subscribe"

**Possible Causes:**
1. Browser doesn't support push notifications
2. Notifications are blocked in browser settings
3. Not using HTTPS (required for push notifications)
4. Service worker not registered

**Solutions:**
- Use Chrome, Firefox, or Edge (best support)
- Check browser notification permissions
- Ensure you're on HTTPS (not localhost in production)
- Check service worker registration in DevTools

### Issue: "Notification received but not displayed"

**Possible Causes:**
1. Browser is in focus (some browsers don't show notifications when tab is active)
2. Do Not Disturb mode is enabled
3. Notification permission was revoked

**Solutions:**
- Minimize browser or switch to another tab
- Check system notification settings
- Re-subscribe to notifications

### Issue: "Subscription saved but no notifications received"

**Possible Causes:**
1. VAPID keys mismatch
2. Subscription expired
3. Backend not sending notifications

**Solutions:**
- Verify VAPID keys in Railway match the ones used to subscribe
- Check backend logs for errors
- Try unsubscribing and re-subscribing
- Test with the admin test endpoint

### Issue: "TypeError: Failed to execute 'subscribe' on 'PushManager'"

**Possible Causes:**
1. VAPID public key format is incorrect
2. Service worker not ready

**Solutions:**
- Verify VAPID public key is a valid hex string
- Wait for service worker to be ready before subscribing
- Check browser console for detailed error messages

## Step 6: Manual Testing Checklist

- [ ] Backend status endpoint returns `enabled: true`
- [ ] VAPID public key endpoint returns a valid key
- [ ] Frontend shows "Push Notifications" section on homepage
- [ ] Browser prompts for notification permission
- [ ] Subscription succeeds and shows success message
- [ ] Subscription appears in database
- [ ] Test notification endpoint sends successfully
- [ ] Notification appears on device
- [ ] Clicking notification opens the correct page
- [ ] Unsubscribe works correctly

## Step 7: Production Testing

Once everything works in testing:

1. **Monitor Subscriptions**: Check database periodically to see subscription count
2. **Monitor Errors**: Check backend logs for push notification errors
3. **Test Real Events**: Wait for actual tournament events and verify notifications are sent
4. **User Feedback**: Ask users to test and report any issues

## Browser Support

| Browser | Desktop | Mobile | Notes |
|---------|---------|--------|-------|
| Chrome | ✅ | ✅ | Full support |
| Firefox | ✅ | ✅ | Full support |
| Edge | ✅ | ✅ | Full support |
| Safari | ✅ | ⚠️ | **iOS 16.4+ only, requires PWA install to home screen** |
| Opera | ✅ | ✅ | Full support |

### ⚠️ Important: Safari on iPhone Limitations

**Safari on iPhone has special requirements for push notifications:**

1. **iOS Version**: Requires iOS 16.4 or later
2. **PWA Installation Required**: Push notifications **DO NOT work** in regular Safari browser on iPhone. The PWA must be:
   - Installed to the home screen (Add to Home Screen)
   - Opened from the home screen icon (not from Safari)
3. **No Browser Support**: Unlike Chrome/Firefox, Safari on iOS does not support push notifications when browsing the website normally

**How to Enable Push Notifications on iPhone:**

1. Open your website in Safari on iPhone
2. Tap the Share button (square with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Give it a name and tap "Add"
5. **Open the app from the home screen icon** (not from Safari)
6. Now you can subscribe to push notifications
7. Notifications will work even when the app is closed

**Alternative for iPhone Users:**

If users can't install the PWA or are on iOS < 16.4, they can:
- Use Chrome or Firefox on iPhone (if available)
- Use the website normally (notifications won't work, but all other features will)

## Next Steps

After successful testing:
1. Monitor subscription growth
2. Test with real tournament events
3. Consider adding notification preferences (users can choose which events to receive)
4. Add analytics to track notification delivery rates
