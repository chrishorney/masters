"""Push notification endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models import PushSubscription
from app.services.push_notifications import get_push_service

logger = logging.getLogger(__name__)

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
    
    try:
        # Check if subscription already exists
        existing = db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint
        ).first()
        
        if existing:
            # Update existing subscription
            existing.subscription_data = subscription
            existing.active = True
            logger.info(f"Updated push subscription: {endpoint[:50]}...")
        else:
            # Create new subscription
            new_subscription = PushSubscription(
                endpoint=endpoint,
                subscription_data=subscription
            )
            db.add(new_subscription)
            logger.info(f"Created new push subscription: {endpoint[:50]}...")
        
        db.commit()
        
        return {"success": True, "message": "Subscribed to push notifications"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error subscribing to push notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error subscribing: {str(e)}")


@router.post("/push/unsubscribe")
async def unsubscribe(
    subscription: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Unsubscribe from push notifications."""
    endpoint = subscription.get("endpoint")
    
    if not endpoint:
        raise HTTPException(status_code=400, detail="Missing endpoint")
    
    try:
        db_sub = db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint
        ).first()
        
        if db_sub:
            db_sub.active = False
            db.commit()
            logger.info(f"Unsubscribed push notification: {endpoint[:50]}...")
            return {"success": True, "message": "Unsubscribed from push notifications"}
        else:
            return {"success": True, "message": "Subscription not found"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error unsubscribing from push notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error unsubscribing: {str(e)}")


@router.get("/push/public-key")
async def get_public_key():
    """Get VAPID public key for frontend."""
    push_service = get_push_service()
    
    if not push_service.enabled or not push_service.vapid_public_key:
        raise HTTPException(
            status_code=503,
            detail="Push notifications are not enabled"
        )
    
    # VAPID public key should be a hex string (65 bytes = 130 hex chars starting with '04')
    # Convert to base64 URL-safe format for frontend
    import base64
    
    public_key_hex = push_service.vapid_public_key
    
    # If it's already hex, convert to bytes then to base64 URL-safe
    try:
        # Remove any whitespace
        public_key_hex = public_key_hex.strip()
        
        # Validate hex string
        if not all(c in '0123456789abcdefABCDEF' for c in public_key_hex):
            raise ValueError(f"Invalid hex characters in VAPID public key. Key length: {len(public_key_hex)}")
        
        # Check expected length (65 bytes = 130 hex chars for uncompressed EC point)
        if len(public_key_hex) != 130:
            logger.warning(f"VAPID public key length is {len(public_key_hex)}, expected 130 hex characters (65 bytes)")
        
        # Convert hex to bytes
        public_key_bytes = bytes.fromhex(public_key_hex)
        
        # Validate byte length
        if len(public_key_bytes) != 65:
            logger.warning(f"VAPID public key byte length is {len(public_key_bytes)}, expected 65 bytes")
        
        # Validate it starts with 0x04 (uncompressed point indicator)
        if public_key_bytes[0] != 0x04:
            logger.warning(f"VAPID public key does not start with 0x04 (uncompressed point), got 0x{public_key_bytes[0]:02x}")
        
        # Convert to base64 URL-safe (no padding)
        public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
        
        logger.debug(f"VAPID public key converted: hex length={len(public_key_hex)}, bytes={len(public_key_bytes)}, base64 length={len(public_key_b64)}")
        
        return {
            "publicKey": public_key_b64,
            "debug": {
                "hex_length": len(public_key_hex),
                "byte_length": len(public_key_bytes),
                "base64_length": len(public_key_b64),
                "starts_with_04": public_key_bytes[0] == 0x04
            } if logger.level <= logging.DEBUG else None
        }
    except (ValueError, AttributeError) as e:
        # If conversion fails, log detailed error
        logger.error(f"Could not convert VAPID public key format: {e}. Key value (first 20 chars): {public_key_hex[:20] if public_key_hex else 'None'}...")
        raise HTTPException(
            status_code=500,
            detail=f"Invalid VAPID public key format: {str(e)}. Please check your VAPID_PUBLIC_KEY environment variable."
        )


@router.get("/push/status")
async def get_push_status():
    """Get push notification service status."""
    push_service = get_push_service()
    
    return {
        "enabled": push_service.enabled,
        "vapid_configured": bool(push_service.vapid_public_key),
        "status": "enabled" if push_service.enabled else "disabled"
    }
