"""Player model - cached player data from API."""
from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Player(Base):
    """Player model - cached player information from Slash Golf API."""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String, unique=True, nullable=False, index=True)  # From API
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    full_name = Column(String, nullable=False, index=True)  # For easy searching
    
    # Cached API data
    api_data = Column(JSON)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Player {self.full_name} ({self.player_id})>"
