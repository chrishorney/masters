"""Push subscription model for PWA notifications."""
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PushSubscription(Base):
    """Push subscription model - stores user push notification subscriptions."""
    __tablename__ = "push_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # Optional - can be anonymous for now
    endpoint = Column(String, nullable=False, unique=True, index=True)
    subscription_data = Column(JSON, nullable=False)  # Full subscription object
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    active = Column(Boolean, default=True)  # Can disable without deleting
    
    def __repr__(self):
        endpoint_short = self.endpoint[:50] + "..." if len(self.endpoint) > 50 else self.endpoint
        return f"<PushSubscription {self.id} - {endpoint_short}>"
