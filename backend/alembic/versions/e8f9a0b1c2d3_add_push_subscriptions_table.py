"""Add push_subscriptions table

Revision ID: e8f9a0b1c2d3
Revises: b2c3d4e5f6a7
Create Date: 2026-01-24 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e8f9a0b1c2d3'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create push_subscriptions table
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('subscription_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index on endpoint
    op.create_index('ix_push_subscriptions_endpoint', 'push_subscriptions', ['endpoint'], unique=True)
    op.create_index('ix_push_subscriptions_id', 'push_subscriptions', ['id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_push_subscriptions_id', table_name='push_subscriptions')
    op.drop_index('ix_push_subscriptions_endpoint', table_name='push_subscriptions')
    
    # Drop table
    op.drop_table('push_subscriptions')
