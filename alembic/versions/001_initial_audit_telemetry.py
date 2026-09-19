"""Initial audit telemetry migration

Revision ID: 001_initial_audit_telemetry
Revises: 
Create Date: 2026-09-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_audit_telemetry'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_telemetry',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_type', sa.String(length=32), nullable=False),
        sa.Column('decision', sa.String(length=16), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('threat_categories', sa.JSON(), nullable=False),
        sa.Column('triggered_rule_ids', sa.JSON(), nullable=False),
        sa.Column('matched_policy_ids', sa.JSON(), nullable=False),
        sa.Column('latency_metrics', sa.JSON(), nullable=False),
        sa.Column('redacted_preview', sa.Text(), nullable=False),
        sa.Column('sanitized_preview', sa.Text(), nullable=True),
        sa.Column('llm', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_telemetry_request_id'), 'audit_telemetry', ['request_id'], unique=False)
    op.create_index(op.f('ix_audit_telemetry_timestamp'), 'audit_telemetry', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_telemetry_timestamp'), table_name='audit_telemetry')
    op.drop_index(op.f('ix_audit_telemetry_request_id'), table_name='audit_telemetry')
    op.drop_table('audit_telemetry')
