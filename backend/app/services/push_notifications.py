"""Push notification service for PWA."""
import logging
import json
from typing import Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Try to import pywebpush, but don't fail if not installed
try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False
    logger.warning("pywebpush not installed. Push notifications will be disabled.")


class PushNotificationService:
    """Service for sending push notifications to PWA users."""
    
    def __init__(self):
        self.enabled = getattr(settings, 'push_notifications_enabled', False) and WEBPUSH_AVAILABLE
        self.vapid_public_key = getattr(settings, 'vapid_public_key', None)
        self.vapid_private_key = getattr(settings, 'vapid_private_key', None)
        self.vapid_email = getattr(settings, 'vapid_email', None)
        
        if self.enabled and not all([self.vapid_public_key, self.vapid_private_key, self.vapid_email]):
            logger.warning("Push notifications enabled but VAPID keys not configured")
            self.enabled = False
        
        # Validate VAPID keys if enabled
        if self.enabled:
            # Validate public key format (should be hex string, 130 chars for 65 bytes)
            if self.vapid_public_key:
                public_key_clean = self.vapid_public_key.strip()
                if len(public_key_clean) != 130:
                    logger.warning(f"VAPID public key length is {len(public_key_clean)}, expected 130 hex characters")
                if not all(c in '0123456789abcdefABCDEF' for c in public_key_clean):
                    logger.warning("VAPID public key contains invalid hex characters")
            
            # Validate private key format (should be hex string, 64 chars for 32 bytes)
            if self.vapid_private_key:
                private_key_clean = self.vapid_private_key.strip()
                if len(private_key_clean) != 64:
                    logger.warning(f"VAPID private key length is {len(private_key_clean)}, expected 64 hex characters")
                if not all(c in '0123456789abcdefABCDEF' for c in private_key_clean):
                    logger.warning("VAPID private key contains invalid hex characters")
            
            # Validate email format
            if self.vapid_email and not self.vapid_email.startswith('mailto:'):
                logger.warning(f"VAPID email should start with 'mailto:', got: {self.vapid_email[:20]}...")
            
            logger.info("Push notification service enabled")
        else:
            logger.debug("Push notification service disabled")
    
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
        
        if not WEBPUSH_AVAILABLE:
            logger.warning("pywebpush not available, cannot send push notification")
            return False
        
        try:
            payload = {
                "title": title,
                "body": body,
                "url": url or "/",
                "icon": icon or "/icon-192x192.png"
            }
            
            # Convert hex string private key to bytes if needed
            private_key = self.vapid_private_key
            if isinstance(private_key, str):
                try:
                    # Try to decode as hex
                    private_key = bytes.fromhex(private_key)
                except ValueError:
                    # If not hex, assume it's already in the right format
                    pass
            
            webpush(
                subscription_info=subscription,
                data=json.dumps(payload),
                vapid_private_key=private_key,
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
