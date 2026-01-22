"""Participant model."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Participant(Base):
    """Participant model - represents a person in the pool."""
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True, index=True)
    entry_date = Column(DateTime, server_default=func.now())
    paid = Column(Boolean, default=False)
    
    # Relationships
    entries = relationship("Entry", back_populates="participant")

    def __repr__(self):
        return f"<Participant {self.name}>"
