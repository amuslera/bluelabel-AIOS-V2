"""
Prepare all models for Alembic migration generation
This script imports all models to ensure they're available for autogenerate
"""

# Import all model definitions to ensure they're registered with Base.metadata
from shared.models.user import UserModel
from shared.models.file import FileModel
from services.knowledge.models import ContentItem, Tag, Concept, SearchQuery, Base as KnowledgeBase
from services.workflow.repository import WorkflowDB, WorkflowStepDB, WorkflowExecutionDB, ExecutionStepDB

# Get the metadata
from sqlalchemy import MetaData

# Combine all metadata
combined_metadata = MetaData()

# Import Base from each module that has one
from services.knowledge.models import Base as KnowledgeBase
from shared.models.user import Base as UserBase
from shared.models.file import Base as FileBase
from services.workflow.repository import Base as WorkflowBase

# Get all metadata
all_bases = [KnowledgeBase, UserBase, FileBase, WorkflowBase]

print("Loaded models:")
for base in all_bases:
    print(f"- {base}")
    for table in base.metadata.tables.values():
        print(f"  - Table: {table.name}")