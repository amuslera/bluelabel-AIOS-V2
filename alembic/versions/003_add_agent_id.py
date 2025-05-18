"""Add agent_id column to knowledge_items

Revision ID: 003
Revises: 249f64166921
Create Date: 2025-05-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '249f64166921'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Just add the agent_id column we need
    try:
        op.add_column('knowledge_items', sa.Column('agent_id', sa.String(length=255), nullable=False, default='legacy'))
    except Exception:
        # Column might already exist
        pass


def downgrade() -> None:
    try:
        op.drop_column('knowledge_items', 'agent_id')
    except Exception:
        pass