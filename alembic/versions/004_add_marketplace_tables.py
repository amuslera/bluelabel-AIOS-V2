"""Add marketplace tables

Revision ID: 004_add_marketplace_tables
Revises: 249f64166921
Create Date: 2025-06-01 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004_add_marketplace_tables'
down_revision = '249f64166921'
branch_labels = None
depends_on = None


def upgrade():
    """Add marketplace tables"""
    
    # Create agent categories table
    op.create_table(
        'agent_categories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(100), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create agent tags table
    op.create_table(
        'agent_tags',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create marketplace agents table
    op.create_table(
        'marketplace_agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author_id', sa.String(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('icon_url', sa.String(512), nullable=True),
        sa.Column('repository_url', sa.String(512), nullable=True),
        sa.Column('agent_type', sa.String(100), nullable=True),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('requirements', sa.JSON(), nullable=True),
        sa.Column('configuration_schema', sa.JSON(), nullable=True),
        sa.Column('pricing_model', sa.String(50), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('license', sa.String(100), nullable=True),
        sa.Column('install_count', sa.Integer(), nullable=True),
        sa.Column('rating_average', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agent installations table
    op.create_table(
        'agent_installations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('installed_version', sa.String(50), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('installed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['marketplace_agents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agent reviews table
    op.create_table(
        'agent_reviews',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('helpful_count', sa.Integer(), nullable=True),
        sa.Column('is_verified_purchase', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['marketplace_agents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agent analytics table
    op.create_table(
        'agent_analytics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('referrer', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['marketplace_agents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_marketplace_agents_category', 'marketplace_agents', ['category'])
    op.create_index('idx_marketplace_agents_pricing', 'marketplace_agents', ['pricing_model'])
    op.create_index('idx_marketplace_agents_active', 'marketplace_agents', ['is_active'])
    op.create_index('idx_marketplace_agents_featured', 'marketplace_agents', ['is_featured'])
    op.create_index('idx_marketplace_agents_rating', 'marketplace_agents', ['rating_average'])
    op.create_index('idx_marketplace_agents_installs', 'marketplace_agents', ['install_count'])
    
    op.create_index('idx_agent_installations_user', 'agent_installations', ['user_id'])
    op.create_index('idx_agent_installations_agent', 'agent_installations', ['agent_id'])
    op.create_index('idx_agent_installations_active', 'agent_installations', ['is_active'])
    
    op.create_index('idx_agent_reviews_agent', 'agent_reviews', ['agent_id'])
    op.create_index('idx_agent_reviews_user', 'agent_reviews', ['user_id'])
    op.create_index('idx_agent_reviews_rating', 'agent_reviews', ['rating'])
    
    op.create_index('idx_agent_analytics_agent', 'agent_analytics', ['agent_id'])
    op.create_index('idx_agent_analytics_event', 'agent_analytics', ['event_type'])
    op.create_index('idx_agent_analytics_created', 'agent_analytics', ['created_at'])


def downgrade():
    """Remove marketplace tables"""
    
    # Drop indexes
    op.drop_index('idx_agent_analytics_created', table_name='agent_analytics')
    op.drop_index('idx_agent_analytics_event', table_name='agent_analytics')
    op.drop_index('idx_agent_analytics_agent', table_name='agent_analytics')
    
    op.drop_index('idx_agent_reviews_rating', table_name='agent_reviews')
    op.drop_index('idx_agent_reviews_user', table_name='agent_reviews')
    op.drop_index('idx_agent_reviews_agent', table_name='agent_reviews')
    
    op.drop_index('idx_agent_installations_active', table_name='agent_installations')
    op.drop_index('idx_agent_installations_agent', table_name='agent_installations')
    op.drop_index('idx_agent_installations_user', table_name='agent_installations')
    
    op.drop_index('idx_marketplace_agents_installs', table_name='marketplace_agents')
    op.drop_index('idx_marketplace_agents_rating', table_name='marketplace_agents')
    op.drop_index('idx_marketplace_agents_featured', table_name='marketplace_agents')
    op.drop_index('idx_marketplace_agents_active', table_name='marketplace_agents')
    op.drop_index('idx_marketplace_agents_pricing', table_name='marketplace_agents')
    op.drop_index('idx_marketplace_agents_category', table_name='marketplace_agents')
    
    # Drop tables in reverse order (due to foreign keys)
    op.drop_table('agent_analytics')
    op.drop_table('agent_reviews')
    op.drop_table('agent_installations')
    op.drop_table('marketplace_agents')
    op.drop_table('agent_tags')
    op.drop_table('agent_categories')