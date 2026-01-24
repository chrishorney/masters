# PWA Push Notifications Setup Guide

This is a step-by-step guide to implement push notifications for the PWA. The service worker is already set up to handle push notifications - we just need to add the backend integration.

## Overview

Push notifications allow the app to send notifications to users even when the app is closed. This uses the **Web Push Protocol** with **VAPID** (Voluntary Application Server Identification) keys.

## Architecture

```
Event Occurs (e.g., hole-in-one)
    ↓
Backend detects event
    ↓
Backend sends push notification via Web Push API
    ↓
Push Service (browser vendor: Chrome, Firefox, etc.)
    ↓
User's device receives notification
    ↓
Service Worker displays notification
```

## Step-by-Step Implementation

### Step 1: Generate VAPID Keys

VAPID keys are used to identify your server to push services. You need to generate a public/private key pair.

**Option A: Using Python (Recommended)**

```bash
# Install pywebpush if not already installed
pip3 install pywebpush

# Generate VAPID keys
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

**Option B: Using Node.js**

```bash
npm install web-push -g
web-push generate-vapid-keys
```

**Option C: Online Tool**
- Go to https://web-push-codelab.glitch.me/
- Click "Generate VAPID Keys"
- Copy the keys

**Save the keys** - you'll need:
- Public Key (starts with `BN` or hex string)
- Private Key (hex string)
- Email (format: `mailto:your-email@example.com`)

### Step 2: Add VAPID Keys to Environment Variables

Add to Railway environment variables (or `.env` file):

```bash
VAPID_PUBLIC_KEY=your_public_key_here
VAPID_PRIVATE_KEY=your_private_key_here
VAPID_EMAIL=mailto:your-email@example.com
PUSH_NOTIFICATIONS_ENABLED=true
```

### Step 3: Install Backend Dependencies

Add the web push library to backend:

```bash
cd backend
pip install pywebpush
```

Add to `backend/requirements.txt`:
```
pywebpush>=1.14.0
```

### Step 4: Create Push Notification Service

Create `backend/app/services/push_notifications.py`:

```python
"""Push notification service for PWA."""
import logging
import json
from typing import Dict, List, Optional
from pywebpush import webpush, WebPushException
from app.config import settings

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications to PWA users."""
    
    def __init__(self):
        self.enabled = getattr(settings, 'push_notifications_enabled', False)
        self.vapid_public_key = getattr(settings, 'vapid_public_key', None)
        self.vapid_private_key = getattr(settings, 'vapid_private_key', None)
        self.vapid_email = getattr(settings, 'vapid_email', None)
        
        if self.enabled and not all([self.vapid_public_key, self.vapid_private_key, self.vapid_email]):
            logger.warning("Push notifications enabled but VAPID keys not configured")
            self.enabled = False
    
    def send_notification(
        self,
        subscription: Dict,
        title: str,
        body: str,
        url: Optional[str] = None,
        icon: Optional[str] = None
    ) -> bool:
        """
        Send a push notification to a subscription.
        
        Args:
            subscription: Push subscription object from frontend
            title: Notification title
            body: Notification body
            url: URL to open when notification is clicked
            icon: Icon URL for notification
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            payload = {
                "title": title,
                "body": body,
                "url": url or "/",
                "icon": icon or "/icon-192x192.png"
            }
            
            webpush(
                subscription_info=subscription,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": self.vapid_email
                }
            )
            
            logger.debug(f"Push notification sent: {title}")
            return True
            
        except WebPushException as e:
            if e.response and e.response.status_code == 410:
                # Subscription expired or invalid
                logger.warning(f"Push subscription expired: {subscription.get('endpoint', 'unknown')}")
            else:
                logger.warning(f"Push notification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending push notification: {e}", exc_info=True)
            return False
    
    def send_to_multiple(
        self,
        subscriptions: List[Dict],
        title: str,
        body: str,
        url: Optional[str] = None
    ) -> int:
        """
        Send notification to multiple subscriptions.
        
        Returns:
            Number of successful sends
        """
        success_count = 0
        for subscription in subscriptions:
            if self.send_notification(subscription, title, body, url):
                success_count += 1
        return success_count


# Global instance
_push_service: Optional[PushNotificationService] = None


def get_push_service() -> PushNotificationService:
    """Get or create push notification service instance."""
    global _push_service
    if _push_service is None:
        _push_service = PushNotificationService()
    return _push_service
```

### Step 5: Add VAPID Settings to Config

Update `backend/app/config.py`:

```python
# Push Notifications (PWA)
push_notifications_enabled: bool = False
vapid_public_key: Optional[str] = None
vapid_private_key: Optional[str] = None
vapid_email: Optional[str] = None
```

Update `backend/env.template`:

```bash
# Push Notifications (PWA)
PUSH_NOTIFICATIONS_ENABLED=false
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_EMAIL=mailto:your-email@example.com
```

### Step 6: Create Database Model for Subscriptions

Create `backend/app/models/push_subscription.py`:

```python
"""Push subscription model for PWA notifications."""
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PushSubscription(Base):
    """Push subscription model - stores user push notification subscriptions."""
    __tablename__ = "push_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("participants.id"), nullable=True)  # Optional - can be anonymous
    endpoint = Column(String, nullable=False, unique=True, index=True)
    subscription_data = Column(JSON, nullable=False)  # Full subscription object
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    active = Column(Boolean, default=True)  # Can disable without deleting
    
    def __repr__(self):
        return f"<PushSubscription {self.id} - {self.endpoint[:50]}...>"
```

Create migration:
```bash
cd backend
alembic revision -m "add_push_subscriptions_table"
```

### Step 7: Create API Endpoints

Create `backend/app/api/public/push.py`:

```python
"""Push notification endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models import PushSubscription
from app.services.push_notifications import get_push_service

router = APIRouter()


@router.post("/push/subscribe")
async def subscribe(
    subscription: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Subscribe a user to push notifications.
    
    Request body:
    {
        "endpoint": "https://...",
        "keys": {
            "p256dh": "...",
            "auth": "..."
        }
    }
    """
    push_service = get_push_service()
    
    if not push_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Push notifications are not enabled"
        )
    
    endpoint = subscription.get("endpoint")
    if not endpoint:
        raise HTTPException(status_code=400, detail="Missing endpoint")
    
    # Check if subscription already exists
    existing = db.query(PushSubscription).filter(
        PushSubscription.endpoint == endpoint
    ).first()
    
    if existing:
        # Update existing subscription
        existing.subscription_data = subscription
        existing.active = True
    else:
        # Create new subscription
        new_subscription = PushSubscription(
            endpoint=endpoint,
            subscription_data=subscription
        )
        db.add(new_subscription)
    
    db.commit()
    
    return {"success": True, "message": "Subscribed to push notifications"}


@router.post("/push/unsubscribe")
async def unsubscribe(
    subscription: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Unsubscribe from push notifications."""
    endpoint = subscription.get("endpoint")
    
    if endpoint:
        db_sub = db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint
        ).first()
        
        if db_sub:
            db_sub.active = False
            db.commit()
    
    return {"success": True, "message": "Unsubscribed from push notifications"}


@router.get("/push/public-key")
async def get_public_key():
    """Get VAPID public key for frontend."""
    push_service = get_push_service()
    
    if not push_service.enabled or not push_service.vapid_public_key:
        raise HTTPException(
            status_code=503,
            detail="Push notifications are not enabled"
        )
    
    return {"publicKey": push_service.vapid_public_key}
```

Register in `backend/app/main.py`:
```python
from app.api.public import push
app.include_router(push.router, prefix=settings.api_prefix, tags=["push"])
```

### Step 8: Frontend Subscription

Create `frontend/src/utils/pushNotifications.ts`:

```typescript
/**
 * Push notification utilities
 */

export interface PushSubscriptionData {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

/**
 * Request notification permission
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    console.log('This browser does not support notifications');
    return 'denied';
  }

  if (Notification.permission === 'granted') {
    return 'granted';
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission;
  }

  return Notification.permission;
}

/**
 * Get VAPID public key from server
 */
export async function getVAPIDPublicKey(): Promise<string> {
  const response = await fetch('/api/push/public-key');
  const data = await response.json();
  return data.publicKey;
}

/**
 * Subscribe to push notifications
 */
export async function subscribeToPushNotifications(): Promise<PushSubscriptionData | null> {
  try {
    // Request permission
    const permission = await requestNotificationPermission();
    if (permission !== 'granted') {
      console.log('Notification permission denied');
      return null;
    }

    // Get VAPID public key
    const publicKey = await getVAPIDPublicKey();
    
    // Convert VAPID key to Uint8Array
    const applicationServerKey = urlBase64ToUint8Array(publicKey);

    // Register service worker
    const registration = await navigator.serviceWorker.ready;

    // Subscribe to push
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey,
    });

    // Convert subscription to object
    const subscriptionData: PushSubscriptionData = {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: arrayBufferToBase64(subscription.getKey('p256dh')!),
        auth: arrayBufferToBase64(subscription.getKey('auth')!),
      },
    };

    // Send subscription to server
    await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(subscriptionData),
    });

    console.log('Subscribed to push notifications');
    return subscriptionData;
  } catch (error) {
    console.error('Error subscribing to push notifications:', error);
    return null;
  }
}

/**
 * Unsubscribe from push notifications
 */
export async function unsubscribeFromPushNotifications(): Promise<boolean> {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      await subscription.unsubscribe();

      // Notify server
      await fetch('/api/push/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint,
        }),
      });

      console.log('Unsubscribed from push notifications');
      return true;
    }
    return false;
  } catch (error) {
    console.error('Error unsubscribing from push notifications:', error);
    return false;
  }
}

/**
 * Convert VAPID key from base64 URL to Uint8Array
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/**
 * Convert ArrayBuffer to base64
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}
```

### Step 9: Add Subscription UI Component

Create `frontend/src/components/PushNotificationSettings.tsx`:

```typescript
import { useState, useEffect } from 'react';
import {
  subscribeToPushNotifications,
  unsubscribeFromPushNotifications,
  requestNotificationPermission,
} from '../utils/pushNotifications';

export function PushNotificationSettings() {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>('default');

  useEffect(() => {
    checkSubscriptionStatus();
    setPermission(Notification.permission);
  }, []);

  const checkSubscriptionStatus = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      setIsSubscribed(!!subscription);
    } catch (error) {
      console.error('Error checking subscription:', error);
    }
  };

  const handleSubscribe = async () => {
    setIsLoading(true);
    try {
      const subscription = await subscribeToPushNotifications();
      setIsSubscribed(!!subscription);
      setPermission(Notification.permission);
    } catch (error) {
      console.error('Error subscribing:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    setIsLoading(true);
    try {
      await unsubscribeFromPushNotifications();
      setIsSubscribed(false);
    } catch (error) {
      console.error('Error unsubscribing:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!('Notification' in window) || !('serviceWorker' in navigator)) {
    return null; // Not supported
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Push Notifications
      </h3>
      
      {permission === 'denied' && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            Notifications are blocked. Please enable them in your browser settings.
          </p>
        </div>
      )}

      {isSubscribed ? (
        <div>
          <p className="text-sm text-gray-600 mb-4">
            You're subscribed to push notifications. You'll receive alerts for:
          </p>
          <ul className="text-sm text-gray-600 mb-4 list-disc list-inside space-y-1">
            <li>Hole-in-ones</li>
            <li>Eagles and double eagles</li>
            <li>New leader announcements</li>
            <li>Big position changes</li>
            <li>Round completions</li>
          </ul>
          <button
            onClick={handleUnsubscribe}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {isLoading ? 'Unsubscribing...' : 'Unsubscribe'}
          </button>
        </div>
      ) : (
        <div>
          <p className="text-sm text-gray-600 mb-4">
            Get real-time notifications for exciting tournament events!
          </p>
          <button
            onClick={handleSubscribe}
            disabled={isLoading || permission === 'denied'}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {isLoading ? 'Subscribing...' : 'Enable Notifications'}
          </button>
        </div>
      )}
    </div>
  );
}
```

Add to `frontend/src/pages/HomePage.tsx` or create a settings page.

### Step 10: Integrate with Existing Notification System

Update `backend/app/services/scoring.py` to also send push notifications:

```python
# In _notify_discord_bonus_async, also send push notifications
async def notify_push_bonus_async(self, bonus, round_id, tournament):
    """Send push notification for bonus (fire-and-forget)."""
    try:
        from app.services.push_notifications import get_push_service
        from app.models import PushSubscription
        
        push_service = get_push_service()
        if not push_service.enabled:
            return
        
        # Get all active subscriptions
        subscriptions = self.db.query(PushSubscription).filter(
            PushSubscription.active == True
        ).all()
        
        if not subscriptions:
            return
        
        # Format notification
        bonus_type = bonus.get("bonus_type")
        player_name = "Player"  # Get from player_id
        
        if bonus_type == "hole_in_one":
            title = "🎯 Hole-in-One!"
            body = f"{player_name} just got a hole-in-one!"
        elif bonus_type == "double_eagle":
            title = "🦅 Double Eagle!"
            body = f"{player_name} got a double eagle!"
        elif bonus_type == "eagle":
            title = "🦅 Eagle!"
            body = f"{player_name} got an eagle!"
        else:
            return
        
        # Send to all subscribers
        for sub in subscriptions:
            push_service.send_notification(
                subscription=sub.subscription_data,
                title=title,
                body=body,
                url=f"/leaderboard"
            )
    except Exception as e:
        logger.warning(f"Push notification failed (non-critical): {e}")
```

### Step 11: Test Push Notifications

1. **Enable in Railway**: Set environment variables
2. **Deploy**: Push code to production
3. **Subscribe**: Use the UI to subscribe
4. **Test**: Use admin test endpoint or wait for real events
5. **Verify**: Check that notifications appear

## Testing Checklist

- [ ] VAPID keys generated and added to environment
- [ ] Backend dependencies installed
- [ ] Database migration run
- [ ] API endpoints working
- [ ] Frontend subscription working
- [ ] Service worker receiving push events
- [ ] Notifications displaying correctly
- [ ] Clicking notification opens correct page

## Troubleshooting

### Notifications Not Appearing
- Check browser console for errors
- Verify service worker is active
- Check notification permission is granted
- Verify VAPID keys are correct

### Subscription Failing
- Check VAPID public key format
- Verify endpoint is accessible
- Check browser support (Chrome, Firefox, Edge work best)

### Backend Errors
- Verify VAPID keys in environment variables
- Check pywebpush is installed
- Verify database migration ran

## Next Steps After Setup

1. Add subscription UI to homepage or settings
2. Integrate with existing Discord notification triggers
3. Test with real tournament events
4. Monitor subscription counts
5. Add unsubscribe functionality

## Notes

- **iOS Safari**: Push notifications require iOS 16.4+ and user must add app to home screen
- **Android Chrome**: Full support
- **Desktop**: Works in Chrome, Edge, Firefox
- **Privacy**: Subscriptions are stored but can be deleted
- **Rate Limiting**: Browser push services have rate limits
