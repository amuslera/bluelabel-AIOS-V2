"""
Factory for selecting appropriate content extractor.
"""
from typing import List
from services.extractors.base import BaseExtractor
from services.extractors.text_extractor import TextExtractor


class ExtractorFactory:
    """Factory for creating content extractors"""
    
    def __init__(self):
        self.extractors: List[BaseExtractor] = [
            TextExtractor(),
            # PDFExtractor(),  # To be implemented
            # AudioExtractor(),  # To be implemented
            # URLExtractor(),  # To be implemented
        ]
    
    def get_extractor(self, content_type: str) -> BaseExtractor:
        """
        Get appropriate extractor for content type.
        
        Args:
            content_type: MIME type of the content
            
        Returns:
            Appropriate extractor instance
            
        Raises:
            ValueError: If no extractor supports the content type
        """
        for extractor in self.extractors:
            if extractor.supports_type(content_type):
                return extractor
        
        # Default to text extractor for unknown types
        return TextExtractor()


# Global factory instance
_factory = ExtractorFactory()


def get_extractor(content_type: str) -> BaseExtractor:
    """Get extractor for content type"""
    return _factory.get_extractor(content_type)