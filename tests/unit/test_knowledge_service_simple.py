"""
Simple unit test for Knowledge Service
"""

from services.knowledge.models import SourceType, ContentType


def test_enums():
    """Test that enums are properly defined."""
    assert SourceType.PDF.value == "pdf"
    assert SourceType.EMAIL.value == "email"
    assert ContentType.SUMMARY.value == "summary"
    assert ContentType.EXTRACTION.value == "extraction"
    
    
def test_knowledge_item_model():
    """Test that the model can be imported."""
    from services.knowledge.models import KnowledgeItem
    assert KnowledgeItem.__tablename__ == "knowledge_items"