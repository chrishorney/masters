"""DailyScore model."""
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class DailyScore(Base):
    """DailyScore model - stores calculated scores for each entry per day."""
    __tablename__ = "daily_scores"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    round_id = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Scoring breakdown
    base_points = Column(Float, default=0.0)  # Position-based points
    bonus_points = Column(Float, default=0.0)  # Bonus points earned
    total_points = Column(Float, default=0.0)  # Total for this day
    
    # Detailed breakdown (JSON)
    details = Column(JSON)  # {"player1": {"position": 5, "points": 8}, ...}
    
    calculated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entry = relationship("Entry", back_populates="daily_scores")

    def __repr__(self):
        return f"<DailyScore Entry {self.entry_id} Round {self.round_id} - {self.total_points} pts>"
