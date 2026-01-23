"""RankingSnapshot model - tracks entry positions over time."""
from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RankingSnapshot(Base):
    """RankingSnapshot model - tracks entry positions throughout tournament."""
    __tablename__ = "ranking_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    round_id = Column(Integer, nullable=False, index=True)
    
    # Position data
    position = Column(Integer, nullable=False)  # 1st, 2nd, 3rd, etc.
    total_points = Column(Float, nullable=False)  # Total points at this moment
    points_behind_leader = Column(Float)  # How many points behind 1st place
    
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    tournament = relationship("Tournament", back_populates="ranking_snapshots")
    entry = relationship("Entry", back_populates="ranking_snapshots")
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_tournament_timestamp', 'tournament_id', 'timestamp'),
        Index('idx_entry_tournament', 'entry_id', 'tournament_id'),
        Index('idx_tournament_round', 'tournament_id', 'round_id'),
    )

    def __repr__(self):
        return f"<RankingSnapshot Entry {self.entry_id} Position {self.position} Round {self.round_id}>"
