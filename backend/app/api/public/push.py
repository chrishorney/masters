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
    
    return {"publicKey": push_service.vapid_public_key}


@router.get("/push/status")
async def get_push_status():
    """Get push notification service status."""
    push_service = get_push_service()
    
    return {
        "enabled": push_service.enabled,
        "vapid_configured": bool(push_service.vapid_public_key),
        "status": "enabled" if push_service.enabled else "disabled"
    }
