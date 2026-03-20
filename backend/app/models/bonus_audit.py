"""Bonus audit snapshots — stored results of scorecard-based bonus calculations."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BonusAuditRun(Base):
    """
    One execution of the bonus audit for a tournament round.
    Does not modify live BonusPoint rows; used for reconciliation later.
    """

    __tablename__ = "bonus_audit_runs"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False, index=True)
    round_id = Column(Integer, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")  # pending | completed | failed
    trigger_source = Column(String, nullable=False, default="admin")

    players_checked = Column(Integer, nullable=False, default=0)
    scorecards_fetched = Column(Integer, nullable=False, default=0)
    entries_audited = Column(Integer, nullable=False, default=0)
    bonus_lines_count = Column(Integer, nullable=False, default=0)

    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    tournament = relationship("Tournament", backref="bonus_audit_runs")
    lines = relationship(
        "BonusAuditLine",
        back_populates="run",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<BonusAuditRun id={self.id} t={self.tournament_id} r={self.round_id}>"


class BonusAuditLine(Base):
    """Single detected bonus line for an entry within an audit run."""

    __tablename__ = "bonus_audit_lines"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("bonus_audit_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False, index=True)

    participant_name = Column(String, nullable=False)
    player_id = Column(String, nullable=True)
    player_name = Column(String, nullable=True)

    bonus_type = Column(String, nullable=False, index=True)
    points = Column(Float, nullable=False)
    hole = Column(Integer, nullable=True)

    run = relationship("BonusAuditRun", back_populates="lines")
    entry = relationship("Entry", backref="bonus_audit_lines")

    def __repr__(self):
        return f"<BonusAuditLine run={self.run_id} entry={self.entry_id} {self.bonus_type}>"
