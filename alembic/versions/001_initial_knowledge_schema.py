"""Initial knowledge repository schema

Revision ID: 001
Revises: 
Create Date: 2025-05-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tags table
    op.create_table('tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)
    
    # Create content_items table
    op.create_table('content_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=1024), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('tenant_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_content_created_at', 'content_items', ['created_at'], unique=False)
    op.create_index('idx_content_type_user', 'content_items', ['content_type', 'user_id'], unique=False)
    op.create_index('idx_content_user_tenant', 'content_items', ['user_id', 'tenant_id'], unique=False)
    op.create_index(op.f('ix_content_items_content_type'), 'content_items', ['content_type'], unique=False)
    op.create_index(op.f('ix_content_items_embedding_id'), 'content_items', ['embedding_id'], unique=False)
    op.create_index(op.f('ix_content_items_tenant_id'), 'content_items', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_content_items_title'), 'content_items', ['title'], unique=False)
    op.create_index(op.f('ix_content_items_user_id'), 'content_items', ['user_id'], unique=False)
    
    # Create concepts table
    op.create_table('concepts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_concept_name_type', 'concepts', ['name', 'type'], unique=False)
    op.create_index(op.f('ix_concepts_name'), 'concepts', ['name'], unique=False)
    
    # Create content_tags association table
    op.create_table('content_tags',
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('content_id', 'tag_id')
    )
    
    # Create search_queries table
    op.create_table('search_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('results_count', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_search_timestamp', 'search_queries', ['timestamp'], unique=False)
    op.create_index('idx_search_user', 'search_queries', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_search_user', table_name='search_queries')
    op.drop_index('idx_search_timestamp', table_name='search_queries')
    op.drop_table('search_queries')
    
    op.drop_table('content_tags')
    
    op.drop_index(op.f('ix_concepts_name'), table_name='concepts')
    op.drop_index('idx_concept_name_type', table_name='concepts')
    op.drop_table('concepts')
    
    op.drop_index(op.f('ix_content_items_user_id'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_title'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_tenant_id'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_embedding_id'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_content_type'), table_name='content_items')
    op.drop_index('idx_content_user_tenant', table_name='content_items')
    op.drop_index('idx_content_type_user', table_name='content_items')
    op.drop_index('idx_content_created_at', table_name='content_items')
    op.drop_table('content_items')
    
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_table('tags')