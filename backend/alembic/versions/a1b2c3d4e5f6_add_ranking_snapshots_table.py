"""Add ranking_snapshots table

Revision ID: a1b2c3d4e5f6
Revises: fd7c075d609b
Create Date: 2026-01-22 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'fd7c075d609b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ranking_snapshots table
    op.create_table('ranking_snapshots',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tournament_id', sa.Integer(), nullable=False),
    sa.Column('entry_id', sa.Integer(), nullable=False),
    sa.Column('round_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('total_points', sa.Float(), nullable=False),
    sa.Column('points_behind_leader', sa.Float(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ),
    sa.ForeignKeyConstraint(['entry_id'], ['entries.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_ranking_snapshots_id'), 'ranking_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_ranking_snapshots_round_id'), 'ranking_snapshots', ['round_id'], unique=False)
    op.create_index(op.f('ix_ranking_snapshots_timestamp'), 'ranking_snapshots', ['timestamp'], unique=False)
    op.create_index('idx_tournament_timestamp', 'ranking_snapshots', ['tournament_id', 'timestamp'], unique=False)
    op.create_index('idx_entry_tournament', 'ranking_snapshots', ['entry_id', 'tournament_id'], unique=False)
    op.create_index('idx_tournament_round', 'ranking_snapshots', ['tournament_id', 'round_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_tournament_round', table_name='ranking_snapshots')
    op.drop_index('idx_entry_tournament', table_name='ranking_snapshots')
    op.drop_index('idx_tournament_timestamp', table_name='ranking_snapshots')
    op.drop_index(op.f('ix_ranking_snapshots_timestamp'), table_name='ranking_snapshots')
    op.drop_index(op.f('ix_ranking_snapshots_round_id'), table_name='ranking_snapshots')
    op.drop_index(op.f('ix_ranking_snapshots_id'), table_name='ranking_snapshots')
    
    # Drop table
    op.drop_table('ranking_snapshots')
