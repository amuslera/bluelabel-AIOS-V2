"""Add performance indexes

Revision ID: 005
Revises: 004
Create Date: 2025-05-30 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for common query patterns"""
    
    # Marketplace queries
    op.create_index(
        'idx_agents_category_rating',
        'marketplace_agents',
        ['category', 'rating_average'],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_agents_is_active_featured',
        'marketplace_agents',
        ['is_active', 'is_featured'],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_agents_created_at',
        'marketplace_agents',
        ['created_at'],
        postgresql_using='btree'
    )
    
    # User installations
    op.create_index(
        'idx_installations_user_agent',
        'agent_installations',
        ['user_id', 'agent_id'],
        unique=True,
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_installations_is_active',
        'agent_installations',
        ['is_active'],
        postgresql_using='btree'
    )
    
    # Reviews
    op.create_index(
        'idx_reviews_agent_rating',
        'agent_reviews',
        ['agent_id', 'rating'],
        postgresql_using='btree'
    )
    
    # Knowledge repository
    op.create_index(
        'idx_knowledge_user_type',
        'knowledge_entries',
        ['user_id', 'content_type'],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_knowledge_created_at',
        'knowledge_entries',
        ['created_at'],
        postgresql_using='btree'
    )
    
    # User activity
    op.create_index(
        'idx_users_email',
        'users',
        ['email'],
        unique=True,
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_users_created_at',
        'users',
        ['created_at'],
        postgresql_using='btree'
    )


def downgrade():
    """Remove performance indexes"""
    
    # Drop all indexes
    op.drop_index('idx_agents_category_rating', 'marketplace_agents')
    op.drop_index('idx_agents_is_active_featured', 'marketplace_agents')
    op.drop_index('idx_agents_created_at', 'marketplace_agents')
    op.drop_index('idx_installations_user_agent', 'agent_installations')
    op.drop_index('idx_installations_is_active', 'agent_installations')
    op.drop_index('idx_reviews_agent_rating', 'agent_reviews')
    op.drop_index('idx_knowledge_user_type', 'knowledge_entries')
    op.drop_index('idx_knowledge_created_at', 'knowledge_entries')
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_users_created_at', 'users')