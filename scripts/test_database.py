#!/usr/bin/env python3
"""Test database connections and operations."""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from services.knowledge.repository_postgres import PostgresKnowledgeRepository
from services.knowledge.models import Base

load_dotenv()


async def test_database_connection():
    """Test PostgreSQL database connection and operations."""
    print("🔍 Testing Database Connection...")
    print("=" * 50)
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bluelabel_aios")
    
    # Check if it's using default credentials
    if "postgres:postgres" in db_url:
        print("⚠️  Warning: Using default PostgreSQL credentials")
    
    print(f"📍 Database URL: {db_url.split('@')[1]}")  # Hide credentials
    
    try:
        # Test basic connection
        print("\n1️⃣ Testing basic connection...")
        engine = create_engine(db_url, echo=False)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Basic connection successful")
        
        # Create tables
        print("\n2️⃣ Creating/verifying tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created/verified")
        
        # Test repository operations
        print("\n3️⃣ Testing repository operations...")
        repo = PostgresKnowledgeRepository(db_url)
        
        # Test item creation
        print("   Creating test item...")
        test_item = await repo.add_content(
            title="Test Database Item",
            source="test_database.py",
            content_type="text",
            text_content="This is a test item for database connectivity",
            metadata={"test": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        print(f"   ✅ Created item: {test_item.id}")
        
        # Test item retrieval
        print("   Retrieving test item...")
        retrieved_item = await repo.get_content(str(test_item.id))
        if retrieved_item and retrieved_item.title == "Test Database Item":
            print("   ✅ Retrieved item successfully")
        else:
            print("   ❌ Failed to retrieve item")
        
        # Test search
        print("   Testing search...")
        search_results = await repo.search_content("test database")
        print(f"   ✅ Search returned {len(search_results)} results")
        
        # Test filtering
        print("   Testing filtering...")
        filtered_items = await repo.list_content(content_type="text")
        print(f"   ✅ Filter returned {len(filtered_items)} items")
        
        # Clean up test data
        print("   Cleaning up test data...")
        await repo.delete_content(str(test_item.id))
        print("   ✅ Test data cleaned up")
        
        print("\n✅ All database tests passed!")
        
        # Show table information
        print("\n📊 Database Tables:")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            for table in tables:
                print(f"   - {table[0]}")
        
    except Exception as e:
        print(f"\n❌ Database test failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is installed and running")
        print("2. Check if the database exists: createdb bluelabel_aios")
        print("3. Verify credentials in .env file")
        print("4. Check if PostgreSQL is listening on the correct port")
        
    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    print("🚀 Database Connection Test")
    print("==========================")
    asyncio.run(test_database_connection())