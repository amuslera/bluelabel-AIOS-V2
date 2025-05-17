"""
PDF Text Extraction Service
"""
import os
from typing import Optional, Dict, Any
import PyPDF2
import pdfplumber
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
from core.logging import setup_logging

logger = setup_logging(service_name="pdf-extractor")


class PDFExtractor:
    """Extract text content from PDF files"""
    
    def __init__(self):
        self.mime_detector = magic.Magic(mime=True) if HAS_MAGIC else None
    
    def validate_pdf(self, file_path: str) -> bool:
        """
        Validate that the file is a PDF
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is a valid PDF
        """
        try:
            if self.mime_detector:
                mime_type = self.mime_detector.from_file(file_path)
                return mime_type == 'application/pdf'
            else:
                # Fallback to checking file extension
                return file_path.lower().endswith('.pdf')
        except Exception as e:
            logger.error(f"Error validating PDF: {str(e)}")
            # Fallback to extension check
            return file_path.lower().endswith('.pdf')
    
    def extract_text_pypdf2(self, file_path: str) -> Optional[str]:
        """
        Extract text using PyPDF2
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num}: {str(e)}")
                        continue
                
                return text.strip() if text else None
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {str(e)}")
            return None
    
    def extract_text_pdfplumber(self, file_path: str) -> Optional[str]:
        """
        Extract text using pdfplumber (better for complex PDFs)
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            text = ""
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num}: {str(e)}")
                        continue
            
            return text.strip() if text else None
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {str(e)}")
            return None
    
    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF using multiple methods
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with extraction results
        """
        result = {
            "success": False,
            "text": None,
            "metadata": {},
            "error": None
        }
        
        # Validate file
        if not os.path.exists(file_path):
            result["error"] = "File not found"
            return result
        
        if not self.validate_pdf(file_path):
            result["error"] = "Invalid PDF file"
            return result
        
        # Try pdfplumber first (better for complex PDFs)
        text = self.extract_text_pdfplumber(file_path)
        
        # Fallback to PyPDF2 if pdfplumber fails
        if not text:
            logger.info("Falling back to PyPDF2")
            text = self.extract_text_pypdf2(file_path)
        
        if text:
            result["success"] = True
            result["text"] = text
            result["metadata"] = {
                "file_size": os.path.getsize(file_path),
                "extraction_method": "pdfplumber" if self.extract_text_pdfplumber(file_path) else "pypdf2",
                "text_length": len(text),
                "pages": text.count("--- Page") if text else 0
            }
        else:
            result["error"] = "Failed to extract text from PDF"
        
        return result


# Factory function
def get_pdf_extractor() -> PDFExtractor:
    """Get PDF extractor instance"""
    return PDFExtractor()