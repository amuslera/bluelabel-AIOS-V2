#!/usr/bin/env python3
"""Check database schema"""
import asyncio
import os
from sqlalchemy import create_engine, inspect

def check_schema():
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bluelabel_aios")
    engine = create_engine(database_url)
    
    inspector = inspect(engine)
    
    # Check if knowledge_items table exists
    if 'knowledge_items' in inspector.get_table_names():
        print("knowledge_items table exists")
        columns = inspector.get_columns('knowledge_items')
        print("\nColumns:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")
    else:
        print("knowledge_items table does not exist")

if __name__ == "__main__":
    check_schema()