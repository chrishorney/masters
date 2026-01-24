# PWA Push Notifications - Quick Start Guide

## Overview

This is a simplified step-by-step guide to get push notifications working. The full detailed guide is in `PWA_PUSH_NOTIFICATIONS_SETUP.md`.

## Quick Steps Summary

### 1. Generate VAPID Keys (5 minutes)

**Easiest Method - Python:**
```bash
pip3 install pywebpush
python3 -c "
from pywebpush import webpush
import json
from py_vapid import Vapid01

vapid = Vapid01()
private_key = vapid.private_key
public_key = vapid.public_key.public_bytes_raw

print('VAPID_PUBLIC_KEY=' + public_key.hex())
print('VAPID_PRIVATE_KEY=' + private_key.private_bytes_raw().hex())
print('VAPID_EMAIL=mailto:your-email@example.com')
"
```

**Save the output** - you'll add these to Railway environment variables.

### 2. Add to Railway Environment Variables

In Railway dashboard, add:
- `VAPID_PUBLIC_KEY` = (the hex string from step 1)
- `VAPID_PRIVATE_KEY` = (the hex string from step 1)
- `VAPID_EMAIL` = `mailto:your-email@example.com`
- `PUSH_NOTIFICATIONS_ENABLED` = `true`

### 3. Install Backend Dependency

```bash
cd backend
pip install pywebpush
```

Add to `requirements.txt`:
```
pywebpush>=1.14.0
```

### 4. Create Backend Files

I'll create these files for you in the next step. The files needed are:
- `backend/app/services/push_notifications.py` - Push service
- `backend/app/models/push_subscription.py` - Database model
- `backend/app/api/public/push.py` - API endpoints
- Update `backend/app/config.py` - Add VAPID settings
- Database migration for push_subscriptions table

### 5. Create Frontend Files

- `frontend/src/utils/pushNotifications.ts` - Subscription utilities
- `frontend/src/components/PushNotificationSettings.tsx` - UI component

### 6. Integrate with Existing Notifications

Update the existing Discord notification triggers to also send push notifications.

## What I'll Do Next

I can create all the backend and frontend files for you. Just let me know and I'll:
1. Create the push notification service
2. Create the database model and migration
3. Create the API endpoints
4. Create the frontend utilities and UI
5. Integrate with existing notification triggers

Then you just need to:
1. Generate VAPID keys (step 1 above)
2. Add them to Railway
3. Deploy

Would you like me to create all these files now?
