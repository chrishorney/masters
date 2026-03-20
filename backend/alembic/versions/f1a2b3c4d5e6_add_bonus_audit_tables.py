"""Add bonus audit runs and lines tables

Revision ID: f1a2b3c4d5e6
Revises: e8f9a0b1c2d3
Create Date: 2026-03-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "e8f9a0b1c2d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bonus_audit_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("trigger_source", sa.String(), nullable=False),
        sa.Column("players_checked", sa.Integer(), nullable=False),
        sa.Column("scorecards_fetched", sa.Integer(), nullable=False),
        sa.Column("entries_audited", sa.Integer(), nullable=False),
        sa.Column("bonus_lines_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bonus_audit_runs_tournament_id", "bonus_audit_runs", ["tournament_id"])
    op.create_index("ix_bonus_audit_runs_round_id", "bonus_audit_runs", ["round_id"])
    op.create_index("ix_bonus_audit_runs_created_at", "bonus_audit_runs", ["created_at"])

    op.create_table(
        "bonus_audit_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("participant_name", sa.String(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=True),
        sa.Column("player_name", sa.String(), nullable=True),
        sa.Column("bonus_type", sa.String(), nullable=False),
        sa.Column("points", sa.Float(), nullable=False),
        sa.Column("hole", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["entry_id"], ["entries.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["bonus_audit_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bonus_audit_lines_run_id", "bonus_audit_lines", ["run_id"])
    op.create_index("ix_bonus_audit_lines_entry_id", "bonus_audit_lines", ["entry_id"])
    op.create_index("ix_bonus_audit_lines_bonus_type", "bonus_audit_lines", ["bonus_type"])


def downgrade() -> None:
    op.drop_index("ix_bonus_audit_lines_bonus_type", table_name="bonus_audit_lines")
    op.drop_index("ix_bonus_audit_lines_entry_id", table_name="bonus_audit_lines")
    op.drop_index("ix_bonus_audit_lines_run_id", table_name="bonus_audit_lines")
    op.drop_table("bonus_audit_lines")

    op.drop_index("ix_bonus_audit_runs_created_at", table_name="bonus_audit_runs")
    op.drop_index("ix_bonus_audit_runs_round_id", table_name="bonus_audit_runs")
    op.drop_index("ix_bonus_audit_runs_tournament_id", table_name="bonus_audit_runs")
    op.drop_table("bonus_audit_runs")
