"""Make entry player slot columns nullable for manual roster edits

Revision ID: i4j5k6l7m8n9
Revises: h3i4j5k6l7m8
Create Date: 2026-04-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "i4j5k6l7m8n9"
down_revision = "h3i4j5k6l7m8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for col in (
        "player1_id",
        "player2_id",
        "player3_id",
        "player4_id",
        "player5_id",
        "player6_id",
    ):
        op.alter_column(
            "entries",
            col,
            existing_type=sa.String(),
            nullable=True,
        )


def downgrade() -> None:
    for col in (
        "player1_id",
        "player2_id",
        "player3_id",
        "player4_id",
        "player5_id",
        "player6_id",
    ):
        op.alter_column(
            "entries",
            col,
            existing_type=sa.String(),
            nullable=False,
        )
