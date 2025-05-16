"""
Base extractor interface for different file types.
"""
from abc import ABC, abstractmethod
from typing import Union, Dict, Any


class BaseExtractor(ABC):
    """Abstract base class for content extractors"""
    
    @abstractmethod
    def extract(
        self,
        file_data: Union[bytes, str],
        filename: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Extract text content from file data.
        
        Args:
            file_data: Raw file data (bytes) or URL (str)
            filename: Original filename for type hints
            metadata: Additional metadata about the file
            
        Returns:
            Extracted text content
        """
        pass
    
    @abstractmethod
    def supports_type(self, content_type: str) -> bool:
        """Check if this extractor supports the given content type"""
        pass