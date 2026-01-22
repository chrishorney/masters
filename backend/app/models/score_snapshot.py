"""ScoreSnapshot model - stores API data snapshots."""
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ScoreSnapshot(Base):
    """ScoreSnapshot model - stores snapshots of leaderboard/scorecard data from API."""
    __tablename__ = "score_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    round_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    
    # Cached API data
    leaderboard_data = Column(JSON)  # Full leaderboard from API
    scorecard_data = Column(JSON)  # Scorecard data for tracked players
    
    # Relationships
    tournament = relationship("Tournament", back_populates="score_snapshots")

    def __repr__(self):
        return f"<ScoreSnapshot Tournament {self.tournament_id} Round {self.round_id}>"
