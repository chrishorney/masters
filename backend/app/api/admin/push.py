"""Admin endpoints for testing push notifications."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import PushSubscription
from app.services.push_notifications import get_push_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/push/test")
async def test_push_notification(
    message: Optional[str] = Query(None, description="Custom test message"),
    db: Session = Depends(get_db)
):
    """
    Send a test push notification to all active subscribers.
    
    This is useful for testing the push notification system.
    """
    push_service = get_push_service()
    
    if not push_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Push notifications are not enabled"
        )
    
    # Get all active subscriptions
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.active == True
    ).all()
    
    if not subscriptions:
        return {
            "success": False,
            "sent_count": 0,
            "message": "No active subscriptions found. Please subscribe via the website first."
        }
    
    # Send test notification
    test_title = "🧪 Test Notification"
    test_body = message or "This is a test notification from the Eldorado Masters Pool!"
    
    success_count = 0
    errors = []
    
    for sub in subscriptions:
        try:
            success = push_service.send_notification(
                subscription=sub.subscription_data,
                title=test_title,
                body=test_body,
                url="/"
            )
            if success:
                success_count += 1
            else:
                errors.append(f"Failed to send to subscription {sub.id}")
        except Exception as e:
            logger.error(f"Error sending test notification to subscription {sub.id}: {e}")
            errors.append(f"Error for subscription {sub.id}: {str(e)}")
    
    return {
        "success": success_count > 0,
        "sent_count": success_count,
        "total_subscriptions": len(subscriptions),
        "errors": errors if errors else None,
        "message": f"Test notification sent to {success_count} of {len(subscriptions)} subscribers"
    }


@router.get("/push/subscriptions")
async def get_push_subscriptions(
    db: Session = Depends(get_db)
):
    """
    Get list of all push notification subscriptions.
    
    Useful for debugging and monitoring.
    """
    subscriptions = db.query(PushSubscription).all()
    
    return {
        "total": len(subscriptions),
        "active": len([s for s in subscriptions if s.active]),
        "inactive": len([s for s in subscriptions if not s.active]),
        "subscriptions": [
            {
                "id": sub.id,
                "endpoint": sub.endpoint[:50] + "..." if len(sub.endpoint) > 50 else sub.endpoint,
                "active": sub.active,
                "created_at": sub.created_at.isoformat() if sub.created_at else None,
                "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
            }
            for sub in subscriptions
        ]
    }
