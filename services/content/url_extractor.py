"""URL content extraction service.

Extracts structured content from URLs including:
- Articles and blog posts
- Documentation pages
- General web pages

Provides clean text and metadata extraction.
"""

import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime

# Import optional libraries with graceful fallback
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False

try:
    from newspaper import Article
    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class URLExtractor:
    """Extracts content from URLs with graceful fallback methods."""
    
    def __init__(self):
        """Initialize the URL extractor."""
        self._check_dependencies()
        
        # Configure html2text if available
        if HAS_HTML2TEXT:
            self.h2t = html2text.HTML2Text()
            self.h2t.ignore_links = False
            self.h2t.ignore_images = False
            self.h2t.ignore_emphasis = False
            self.h2t.skip_internal_links = True
            self.h2t.body_width = 0  # Don't wrap text
    
    def _check_dependencies(self):
        """Check available dependencies and warn about missing ones."""
        missing = []
        
        if not HAS_BS4:
            missing.append("beautifulsoup4")
        if not HAS_HTML2TEXT:
            missing.append("html2text")
        if not HAS_NEWSPAPER:
            missing.append("newspaper3k")
        if not HAS_REQUESTS:
            missing.append("requests")
            
        if missing:
            print(f"Warning: Missing optional dependencies: {', '.join(missing)}")
            print("Install them for better URL extraction capabilities:")
            print(f"pip install {' '.join(missing)}")
    
    def _parse_url(self, url: str) -> Dict[str, Any]:
        """Parse URL to extract metadata."""
        parsed = urlparse(url)
        return {
            "scheme": parsed.scheme,
            "domain": parsed.netloc,
            "path": parsed.path,
            "query": parsed.query,
            "fragment": parsed.fragment
        }
    
    def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL."""
        if not HAS_REQUESTS:
            raise ImportError("requests library is required for fetching URLs")
            
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return None
    
    def _extract_with_newspaper(self, url: str) -> Dict[str, Any]:
        """Extract content using newspaper3k library."""
        if not HAS_NEWSPAPER:
            return {}
            
        try:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()
            
            return {
                "title": article.title,
                "text": article.text,
                "authors": article.authors,
                "publish_date": article.publish_date,
                "top_image": article.top_image,
                "keywords": article.keywords,
                "summary": article.summary,
                "extracted_with": "newspaper3k"
            }
        except Exception as e:
            print(f"Error with newspaper3k extraction: {e}")
            return {}
    
    def _extract_with_beautifulsoup(self, html: str, url: str) -> Dict[str, Any]:
        """Extract content using BeautifulSoup."""
        if not HAS_BS4:
            return {}
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = None
            if soup.title:
                title = soup.title.string
            elif soup.find('h1'):
                title = soup.find('h1').text
                
            # Extract metadata
            description = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content')
                
            # Extract author
            author = None
            for meta_name in ['author', 'article:author', 'twitter:creator']:
                meta_author = soup.find('meta', attrs={'name': meta_name})
                if meta_author:
                    author = meta_author.get('content')
                    break
                    
            # Extract keywords
            keywords = []
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                keywords = [k.strip() for k in meta_keywords.get('content', '').split(',')]
                
            # Extract main content
            # Try different content containers
            content = None
            for tag in ['article', 'main', 'div[role="main"]']:
                element = soup.find(tag)
                if element:
                    content = element.get_text(separator='\n', strip=True)
                    break
                    
            if not content:
                # Fallback to body content
                if soup.body:
                    content = soup.body.get_text(separator='\n', strip=True)
                    
            # Convert to markdown if html2text is available
            if HAS_HTML2TEXT and content:
                try:
                    content = self.h2t.handle(str(soup.find(tag) if tag else soup.body))
                except:
                    pass
                    
            return {
                "title": title,
                "text": content,
                "description": description,
                "author": author,
                "keywords": keywords,
                "extracted_with": "beautifulsoup"
            }
        except Exception as e:
            print(f"Error with BeautifulSoup extraction: {e}")
            return {}
    
    async def extract(self, url: str) -> Dict[str, Any]:
        """Extract content from URL using available methods."""
        result = {
            "url": url,
            "extracted_at": datetime.utcnow().isoformat(),
            "url_metadata": self._parse_url(url),
            "content": {},
            "metadata": {}
        }
        
        # Try newspaper3k first (most feature-rich)
        if HAS_NEWSPAPER:
            newspaper_data = self._extract_with_newspaper(url)
            if newspaper_data.get("text"):
                result["content"].update(newspaper_data)
                result["metadata"]["extraction_method"] = "newspaper3k"
                return result
        
        # Fallback to BeautifulSoup
        html = self._fetch_content(url)
        if html and HAS_BS4:
            bs_data = self._extract_with_beautifulsoup(html, url)
            if bs_data.get("text"):
                result["content"].update(bs_data)
                result["metadata"]["extraction_method"] = "beautifulsoup"
                return result
                
        # Final fallback - raw HTML
        if html:
            result["content"]["raw_html"] = html
            result["metadata"]["extraction_method"] = "raw_html"
        else:
            result["metadata"]["extraction_error"] = "Failed to fetch URL content"
            
        return result
    
    def extract_sync(self, url: str) -> Dict[str, Any]:
        """Synchronous version of extract for compatibility."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.extract(url))
        finally:
            loop.close()


# Example usage
if __name__ == "__main__":
    extractor = URLExtractor()
    
    # Test URL
    test_url = "https://example.com"
    
    # Async usage
    async def test_async():
        result = await extractor.extract(test_url)
        print(f"Title: {result['content'].get('title', 'N/A')}")
        print(f"Text preview: {result['content'].get('text', '')[:200]}...")
        print(f"Extracted with: {result['metadata'].get('extraction_method', 'N/A')}")
    
    # Sync usage
    result = extractor.extract_sync(test_url)
    print(f"\nSync extraction - Title: {result['content'].get('title', 'N/A')}")
    
    # Run async test
    asyncio.run(test_async())