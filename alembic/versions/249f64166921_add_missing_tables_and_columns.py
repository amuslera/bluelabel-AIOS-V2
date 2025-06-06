"""Add missing tables and columns

Revision ID: 249f64166921
Revises: 001
Create Date: 2025-05-17 11:37:35.431167

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '249f64166921'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
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
    op.create_index(op.f('ix_search_queries_user_id'), 'search_queries', ['user_id'], unique=False)
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
    op.create_table('content_tags',
    sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
    sa.PrimaryKeyConstraint('content_id', 'tag_id')
    )
    op.create_table('workflow_executions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('workflow_id', sa.UUID(), nullable=False),
    sa.Column('workflow_version', sa.String(length=50), nullable=True),
    sa.Column('input_data_json', sa.Text(), nullable=True),
    sa.Column('output_data_json', sa.Text(), nullable=True),
    sa.Column('context_json', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'PAUSED', name='workflowstatus'), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('current_step_index', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.String(length=255), nullable=True),
    sa.Column('triggered_by', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('metadata_json', sa.Text(), nullable=True),
    sa.Column('tags_json', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('execution_steps',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('execution_id', sa.UUID(), nullable=False),
    sa.Column('step_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'SKIPPED', 'CANCELLED', name='stepstatus'), nullable=False),
    sa.Column('input_json', sa.Text(), nullable=True),
    sa.Column('output_json', sa.Text(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('attempts', sa.Integer(), nullable=True),
    sa.Column('last_retry_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('knowledge_item_tags')
    op.drop_index('idx_digests_tenant_id', table_name='digests')
    op.drop_index('idx_digests_user_id', table_name='digests')
    op.drop_table('digests')
    op.drop_index('idx_llm_usage_created_at', table_name='llm_usage')
    op.drop_index('idx_llm_usage_tenant_id', table_name='llm_usage')
    op.drop_index('idx_llm_usage_user_id', table_name='llm_usage')
    op.drop_table('llm_usage')
    op.drop_index('idx_knowledge_items_tenant_id', table_name='knowledge_items')
    op.drop_index('idx_knowledge_items_user_id', table_name='knowledge_items')
    op.drop_table('knowledge_items')
    op.alter_column('files', 'status',
               existing_type=postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='file_status'),
               type_=sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='filestatus'),
               existing_nullable=False,
               existing_server_default=sa.text("'pending'::file_status"))
    op.drop_index('idx_files_status', table_name='files')
    op.drop_index('idx_files_tenant_id', table_name='files')
    op.drop_index('idx_files_user_id', table_name='files')
    op.drop_constraint('files_user_id_fkey', 'files', type_='foreignkey')
    op.create_foreign_key(None, 'files', 'users', ['user_id'], ['id'])
    op.add_column('tags', sa.Column('description', sa.Text(), nullable=True))
    op.alter_column('tags', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False,
               existing_server_default=sa.text('now()'))
    op.drop_constraint('uq_tags_name_tenant', 'tags', type_='unique')
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)
    op.drop_column('tags', 'tenant_id')
    op.drop_index('idx_users_tenant_id', table_name='users')
    op.add_column('workflow_steps', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('workflow_steps', sa.Column('agent_type', sa.Enum('CONTENT_MIND', 'CONTEXT_MIND', 'GATEWAY', 'WEB_FETCHER', 'OUTREACH_ASSISTANT', name='agenttype'), nullable=False))
    op.add_column('workflow_steps', sa.Column('input_mappings_json', sa.Text(), nullable=True))
    op.add_column('workflow_steps', sa.Column('output_mappings_json', sa.Text(), nullable=True))
    op.add_column('workflow_steps', sa.Column('condition', sa.Text(), nullable=True))
    op.add_column('workflow_steps', sa.Column('timeout', sa.Integer(), nullable=True))
    op.add_column('workflow_steps', sa.Column('retries', sa.Integer(), nullable=True))
    op.add_column('workflow_steps', sa.Column('retry_delay', sa.Integer(), nullable=True))
    op.add_column('workflow_steps', sa.Column('on_failure', sa.String(length=50), nullable=True))
    op.add_column('workflow_steps', sa.Column('on_timeout', sa.String(length=50), nullable=True))
    op.add_column('workflow_steps', sa.Column('metadata_json', sa.Text(), nullable=True))
    op.add_column('workflow_steps', sa.Column('tags_json', sa.Text(), nullable=True))
    op.drop_index('idx_workflow_steps_workflow_id', table_name='workflow_steps')
    op.drop_constraint('workflow_steps_workflow_id_fkey', 'workflow_steps', type_='foreignkey')
    op.create_foreign_key(None, 'workflow_steps', 'workflows', ['workflow_id'], ['id'])
    op.drop_column('workflow_steps', 'completed_at')
    op.drop_column('workflow_steps', 'started_at')
    op.drop_column('workflow_steps', 'input_data')
    op.drop_column('workflow_steps', 'error_message')
    op.drop_column('workflow_steps', 'output_data')
    op.drop_column('workflow_steps', 'status')
    op.add_column('workflows', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('workflows', sa.Column('version', sa.String(length=50), nullable=False))
    op.add_column('workflows', sa.Column('max_parallel_steps', sa.Integer(), nullable=True))
    op.add_column('workflows', sa.Column('timeout', sa.Integer(), nullable=True))
    op.add_column('workflows', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('workflows', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('workflows', sa.Column('created_by', sa.String(length=255), nullable=True))
    op.add_column('workflows', sa.Column('metadata_json', sa.Text(), nullable=True))
    op.add_column('workflows', sa.Column('tags_json', sa.Text(), nullable=True))
    op.add_column('workflows', sa.Column('active', sa.Boolean(), nullable=True))
    op.add_column('workflows', sa.Column('draft', sa.Boolean(), nullable=True))
    op.drop_index('idx_workflows_status', table_name='workflows')
    op.drop_index('idx_workflows_user_id', table_name='workflows')
    op.drop_constraint('workflows_user_id_fkey', 'workflows', type_='foreignkey')
    op.drop_column('workflows', 'completed_at')
    op.drop_column('workflows', 'started_at')
    op.drop_column('workflows', 'user_id')
    op.drop_column('workflows', 'metadata')
    op.drop_column('workflows', 'tenant_id')
    op.drop_column('workflows', 'error_message')
    op.drop_column('workflows', 'status')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('workflows', sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', name='workflow_status'), server_default=sa.text("'pending'::workflow_status"), autoincrement=False, nullable=False))
    op.add_column('workflows', sa.Column('error_message', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('workflows', sa.Column('tenant_id', sa.UUID(), autoincrement=False, nullable=False))
    op.add_column('workflows', sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('workflows', sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False))
    op.add_column('workflows', sa.Column('started_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('workflows', sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.create_foreign_key('workflows_user_id_fkey', 'workflows', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_workflows_user_id', 'workflows', ['user_id'], unique=False)
    op.create_index('idx_workflows_status', 'workflows', ['status'], unique=False)
    op.drop_column('workflows', 'draft')
    op.drop_column('workflows', 'active')
    op.drop_column('workflows', 'tags_json')
    op.drop_column('workflows', 'metadata_json')
    op.drop_column('workflows', 'created_by')
    op.drop_column('workflows', 'updated_at')
    op.drop_column('workflows', 'created_at')
    op.drop_column('workflows', 'timeout')
    op.drop_column('workflows', 'max_parallel_steps')
    op.drop_column('workflows', 'version')
    op.drop_column('workflows', 'description')
    op.add_column('workflow_steps', sa.Column('status', sa.VARCHAR(length=50), server_default=sa.text("'pending'::character varying"), autoincrement=False, nullable=False))
    op.add_column('workflow_steps', sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('workflow_steps', sa.Column('error_message', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('workflow_steps', sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('workflow_steps', sa.Column('started_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('workflow_steps', sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'workflow_steps', type_='foreignkey')
    op.create_foreign_key('workflow_steps_workflow_id_fkey', 'workflow_steps', 'workflows', ['workflow_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_workflow_steps_workflow_id', 'workflow_steps', ['workflow_id'], unique=False)
    op.drop_column('workflow_steps', 'tags_json')
    op.drop_column('workflow_steps', 'metadata_json')
    op.drop_column('workflow_steps', 'on_timeout')
    op.drop_column('workflow_steps', 'on_failure')
    op.drop_column('workflow_steps', 'retry_delay')
    op.drop_column('workflow_steps', 'retries')
    op.drop_column('workflow_steps', 'timeout')
    op.drop_column('workflow_steps', 'condition')
    op.drop_column('workflow_steps', 'output_mappings_json')
    op.drop_column('workflow_steps', 'input_mappings_json')
    op.drop_column('workflow_steps', 'agent_type')
    op.drop_column('workflow_steps', 'description')
    op.create_index('idx_users_tenant_id', 'users', ['tenant_id'], unique=False)
    op.add_column('tags', sa.Column('tenant_id', sa.UUID(), autoincrement=False, nullable=False))
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.create_unique_constraint('uq_tags_name_tenant', 'tags', ['name', 'tenant_id'], postgresql_nulls_not_distinct=False)
    op.alter_column('tags', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False,
               existing_server_default=sa.text('now()'))
    op.drop_column('tags', 'description')
    op.drop_constraint(None, 'files', type_='foreignkey')
    op.create_foreign_key('files_user_id_fkey', 'files', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_files_user_id', 'files', ['user_id'], unique=False)
    op.create_index('idx_files_tenant_id', 'files', ['tenant_id'], unique=False)
    op.create_index('idx_files_status', 'files', ['status'], unique=False)
    op.alter_column('files', 'status',
               existing_type=sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='filestatus'),
               type_=postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='file_status'),
               existing_nullable=False,
               existing_server_default=sa.text("'pending'::file_status"))
    op.create_table('knowledge_items',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(length=500), autoincrement=False, nullable=False),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('summary', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('source_file_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('vector_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['source_file_id'], ['files.id'], name='knowledge_items_source_file_id_fkey', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='knowledge_items_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='knowledge_items_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('idx_knowledge_items_user_id', 'knowledge_items', ['user_id'], unique=False)
    op.create_index('idx_knowledge_items_tenant_id', 'knowledge_items', ['tenant_id'], unique=False)
    op.create_table('llm_usage',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('model', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('tokens_used', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('cost_usd', sa.NUMERIC(precision=10, scale=6), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='llm_usage_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='llm_usage_pkey')
    )
    op.create_index('idx_llm_usage_user_id', 'llm_usage', ['user_id'], unique=False)
    op.create_index('idx_llm_usage_tenant_id', 'llm_usage', ['tenant_id'], unique=False)
    op.create_index('idx_llm_usage_created_at', 'llm_usage', ['created_at'], unique=False)
    op.create_table('digests',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('item_count', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('sent_via', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(length=50), server_default=sa.text("'created'::character varying"), autoincrement=False, nullable=False),
    sa.Column('summary', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='digests_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='digests_pkey')
    )
    op.create_index('idx_digests_user_id', 'digests', ['user_id'], unique=False)
    op.create_index('idx_digests_tenant_id', 'digests', ['tenant_id'], unique=False)
    op.create_table('knowledge_item_tags',
    sa.Column('knowledge_item_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tag_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['knowledge_item_id'], ['knowledge_items.id'], name='knowledge_item_tags_knowledge_item_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name='knowledge_item_tags_tag_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('knowledge_item_id', 'tag_id', name='knowledge_item_tags_pkey')
    )
    op.drop_table('execution_steps')
    op.drop_table('workflow_executions')
    op.drop_table('content_tags')
    op.drop_index(op.f('ix_concepts_name'), table_name='concepts')
    op.drop_index('idx_concept_name_type', table_name='concepts')
    op.drop_table('concepts')
    op.drop_index(op.f('ix_search_queries_user_id'), table_name='search_queries')
    op.drop_index('idx_search_user', table_name='search_queries')
    op.drop_index('idx_search_timestamp', table_name='search_queries')
    op.drop_table('search_queries')
    op.drop_index(op.f('ix_content_items_user_id'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_title'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_tenant_id'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_embedding_id'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_content_type'), table_name='content_items')
    op.drop_index('idx_content_user_tenant', table_name='content_items')
    op.drop_index('idx_content_type_user', table_name='content_items')
    op.drop_index('idx_content_created_at', table_name='content_items')
    op.drop_table('content_items')
    # ### end Alembic commands ###