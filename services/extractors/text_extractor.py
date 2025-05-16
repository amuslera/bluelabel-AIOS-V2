"""
Text file extractor for plain text and simple formats.
"""
from typing import Union, Dict, Any
from services.extractors.base import BaseExtractor


class TextExtractor(BaseExtractor):
    """Extractor for plain text files"""
    
    SUPPORTED_TYPES = [
        "text/plain",
        "text/markdown",
        "text/csv",
        "text/html",
        "application/json"
    ]
    
    def extract(
        self,
        file_data: Union[bytes, str],
        filename: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Extract content from text files"""
        if isinstance(file_data, bytes):
            # Try to decode as UTF-8
            try:
                return file_data.decode('utf-8')
            except UnicodeDecodeError:
                # Try with latin-1 as fallback
                return file_data.decode('latin-1', errors='ignore')
        
        return str(file_data)
    
    def supports_type(self, content_type: str) -> bool:
        """Check if this extractor supports the content type"""
        return content_type.lower() in self.SUPPORTED_TYPES