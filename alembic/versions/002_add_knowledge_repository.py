"""Add knowledge repository tables

Revision ID: 002
Revises: 001_initial_schema
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types first
    op.execute("CREATE TYPE sourcetype AS ENUM ('email', 'whatsapp', 'pdf', 'url', 'manual')")
    op.execute("CREATE TYPE contenttype AS ENUM ('summary', 'transcript', 'extraction', 'note')")
    op.execute("CREATE TYPE knowledgestatus AS ENUM ('draft', 'active', 'archived', 'deleted')")
    op.execute("CREATE TYPE reviewstatus AS ENUM ('pending', 'reviewed', 'approved', 'rejected')")
    op.execute("CREATE TYPE relationshiptype AS ENUM ('derived_from', 'related_to', 'summarizes', 'references')")
    
    # Create knowledge_items table
    op.create_table('knowledge_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('source_type', postgresql.ENUM('email', 'whatsapp', 'pdf', 'url', 'manual', name='sourcetype'), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_metadata', sa.JSON(), nullable=True),
        sa.Column('content_type', postgresql.ENUM('summary', 'transcript', 'extraction', 'note', name='contenttype'), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('content_metadata', sa.JSON(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True, default=list),
        sa.Column('categories', postgresql.ARRAY(sa.Text()), nullable=True, default=list),
        sa.Column('language', sa.String(length=10), nullable=True, default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'archived', 'deleted', name='knowledgestatus'), nullable=False, default='active'),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('review_status', postgresql.ENUM('pending', 'reviewed', 'approved', 'rejected', name='reviewstatus'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['knowledge_items.id'])
    )
    
    # Create indexes for knowledge_items
    op.create_index('idx_knowledge_items_agent_id', 'knowledge_items', ['agent_id'])
    op.create_index('idx_knowledge_items_user_id', 'knowledge_items', ['user_id'])
    op.create_index('idx_knowledge_items_source_type', 'knowledge_items', ['source_type'])
    op.create_index('idx_knowledge_items_content_type', 'knowledge_items', ['content_type'])
    op.create_index('idx_knowledge_items_status', 'knowledge_items', ['status'])
    op.create_index('idx_knowledge_items_created_at', 'knowledge_items', ['created_at'])
    op.create_index('idx_knowledge_items_tags', 'knowledge_items', ['tags'], postgresql_using='gin')
    op.create_index('idx_knowledge_items_categories', 'knowledge_items', ['categories'], postgresql_using='gin')
    op.execute("CREATE INDEX idx_knowledge_items_text_search ON knowledge_items USING gin(to_tsvector('english', content_text))")
    
    # Create knowledge_relationships table
    op.create_table('knowledge_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', postgresql.ENUM('derived_from', 'related_to', 'summarizes', 'references', name='relationshiptype'), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_id'], ['knowledge_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['knowledge_items.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('source_id', 'target_id', 'relationship_type')
    )
    
    # Create indexes for knowledge_relationships
    op.create_index('idx_knowledge_relationships_source_id', 'knowledge_relationships', ['source_id'])
    op.create_index('idx_knowledge_relationships_target_id', 'knowledge_relationships', ['target_id'])
    op.create_index('idx_knowledge_relationships_type', 'knowledge_relationships', ['relationship_type'])
    
    # Create knowledge_attachments table
    op.create_table('knowledge_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('knowledge_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_item_id'], ['knowledge_items.id'], ondelete='CASCADE')
    )
    
    # Create index for knowledge_attachments
    op.create_index('idx_knowledge_attachments_item_id', 'knowledge_attachments', ['knowledge_item_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('knowledge_attachments')
    op.drop_table('knowledge_relationships')
    op.drop_table('knowledge_items')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS relationshiptype")
    op.execute("DROP TYPE IF EXISTS reviewstatus")
    op.execute("DROP TYPE IF EXISTS knowledgestatus")
    op.execute("DROP TYPE IF EXISTS contenttype")
    op.execute("DROP TYPE IF EXISTS sourcetype")