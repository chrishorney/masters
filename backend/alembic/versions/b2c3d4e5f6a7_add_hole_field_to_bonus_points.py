"""Add hole field to bonus_points table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-22 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add hole column to bonus_points table
    op.add_column('bonus_points', sa.Column('hole', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove hole column from bonus_points table
    op.drop_column('bonus_points', 'hole')
