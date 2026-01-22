"""Entry model."""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Entry(Base):
    """Entry model - represents a participant's 6 player picks."""
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    
    # Original 6 players (player IDs from API)
    player1_id = Column(String, nullable=False)
    player2_id = Column(String, nullable=False)
    player3_id = Column(String, nullable=False)
    player4_id = Column(String, nullable=False)
    player5_id = Column(String, nullable=False)
    player6_id = Column(String, nullable=False)
    
    # Re-buy information
    rebuy_player_ids = Column(JSON, default=list)  # List of player IDs for rebuys
    rebuy_type = Column(String, nullable=True)  # "missed_cut" or "underperformer"
    rebuy_original_player_ids = Column(JSON, default=list)  # Original players replaced
    
    # Weekend bonus tracking
    weekend_bonus_earned = Column(Boolean, default=False)
    weekend_bonus_forfeited = Column(Boolean, default=False)  # If underperformer rebuy
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    participant = relationship("Participant", back_populates="entries")
    tournament = relationship("Tournament", back_populates="entries")
    daily_scores = relationship("DailyScore", back_populates="entry", cascade="all, delete-orphan")
    bonus_points = relationship("BonusPoint", back_populates="entry", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Entry {self.id} - Participant {self.participant_id}>"
