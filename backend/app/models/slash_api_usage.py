"""Monthly Slash Golf / RapidAPI request counters (resets each calendar month, US Central)."""
from sqlalchemy import Column, Integer, JSON, UniqueConstraint
from app.database import Base


class SlashApiUsageMonthly(Base):
    """
    One row per calendar month (year + month in America/Chicago).
    Incremented on each successful Slash Golf HTTP call from our API client.
    """

    __tablename__ = "slash_api_usage_monthly"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_slash_api_usage_year_month"),
    )

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    total_requests = Column(Integer, nullable=False, default=0)
    # e.g. {"leaderboard": 120, "scorecard": 4000, "tournament": 120, "schedule": 5, "players": 0}
    by_endpoint = Column(JSON, nullable=False, default=dict)

    def __repr__(self):
        return f"<SlashApiUsageMonthly {self.year}-{self.month:02d} total={self.total_requests}>"
