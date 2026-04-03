"""Add slash_api_usage_monthly table for RapidAPI hit counts

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2026-03-14 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "g2h3i4j5k6l7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "slash_api_usage_monthly",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("total_requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("by_endpoint", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "month", name="uq_slash_api_usage_year_month"),
    )
    op.create_index("ix_slash_api_usage_monthly_year", "slash_api_usage_monthly", ["year"])
    op.create_index("ix_slash_api_usage_monthly_month", "slash_api_usage_monthly", ["month"])
    op.create_index("ix_slash_api_usage_monthly_id", "slash_api_usage_monthly", ["id"])


def downgrade() -> None:
    op.drop_index("ix_slash_api_usage_monthly_id", table_name="slash_api_usage_monthly")
    op.drop_index("ix_slash_api_usage_monthly_month", table_name="slash_api_usage_monthly")
    op.drop_index("ix_slash_api_usage_monthly_year", table_name="slash_api_usage_monthly")
    op.drop_table("slash_api_usage_monthly")
