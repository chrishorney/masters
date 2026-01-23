"""BonusPoint model."""
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BonusPoint(Base):
    """BonusPoint model - tracks individual bonus point awards."""
    __tablename__ = "bonus_points"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    round_id = Column(Integer, nullable=False, index=True)
    bonus_type = Column(String, nullable=False, index=True)
    # Types: "gir_leader", "fairways_leader", "low_score", "eagle", 
    #       "double_eagle", "hole_in_one", "all_make_cut"
    points = Column(Float, nullable=False)
    player_id = Column(String, nullable=True)  # Which player earned it (if applicable)
    hole = Column(Integer, nullable=True)  # Hole number for eagle/albatross/hole-in-one bonuses
    awarded_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    entry = relationship("Entry", back_populates="bonus_points")

    def __repr__(self):
        return f"<BonusPoint Entry {self.entry_id} - {self.bonus_type} ({self.points} pts)>"
