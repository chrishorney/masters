"""Tournament model."""
from sqlalchemy import Column, Integer, String, Date, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Tournament(Base):
    """Tournament model - represents a golf tournament."""
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    tourn_id = Column(String, nullable=False)  # From Slash Golf API
    org_id = Column(String, default="1")  # PGA = 1
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String)  # "Official", "In Progress", etc.
    current_round = Column(Integer, default=1)
    
    # Cached API data
    api_data = Column(JSON)  # Store full tournament data from API
    
    # Relationships
    entries = relationship("Entry", back_populates="tournament")
    score_snapshots = relationship("ScoreSnapshot", back_populates="tournament")

    def __repr__(self):
        return f"<Tournament {self.year} {self.name}>"
