import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Optional
import asyncio
from app.core.config import settings


class CrawlerService:
    """Service for crawling websites and extracting content."""
    
    def __init__(self, base_url: str, max_pages: int = None, max_depth: int = None):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages or settings.MAX_PAGES_PER_SCAN
        self.max_depth = max_depth or settings.MAX_DEPTH
        self.visited_urls: Set[str] = set()
        self.pages_data: List[Dict] = []
        
    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes."""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized.rstrip('/')
    
    def is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain."""
        return urlparse(url).netloc == self.domain
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and should be crawled."""
        parsed = urlparse(url)
        
        # Skip non-http(s) protocols
        if parsed.scheme not in ['http', 'https']:
            return False
            
        # Skip common file extensions
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', 
                          '.zip', '.tar', '.gz', '.doc', '.docx', '.xls', 
                          '.xlsx', '.ppt', '.pptx', '.mp3', '.mp4', '.avi']
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False
            
        return True
    
    async def fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch a single page and extract its content."""
        try:
            async with httpx.AsyncClient(
                timeout=settings.REQUEST_TIMEOUT,
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return {
                        'url': url,
                        'status_code': response.status_code,
                        'title': None,
                        'html_content': None,
                        'text_content': None,
                        'links': [],
                        'meta': {},
                    }
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Extract text content (remove scripts and styles)
                for script in soup(["script", "style", "noscript"]):
                    script.decompose()
                text_content = soup.get_text(separator=' ', strip=True)
                
                # Extract links
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(url, href)
                    if self.is_valid_url(absolute_url):
                        links.append(absolute_url)
                
                # Extract meta information
                meta = {}
                title_tag = soup.find('title')
                meta['title'] = title_tag.string.strip() if title_tag else None
                
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                meta['description'] = meta_desc['content'] if meta_desc and meta_desc.get('content') else None
                
                meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
                meta['keywords'] = meta_keywords['content'] if meta_keywords and meta_keywords.get('content') else None
                
                # Check for favicon
                favicon = soup.find('link', rel=lambda x: x and 'icon' in x.lower())
                meta['has_favicon'] = favicon is not None
                
                return {
                    'url': url,
                    'status_code': response.status_code,
                    'title': meta['title'],
                    'html_content': str(soup),
                    'text_content': text_content,
                    'links': links,
                    'meta': meta,
                }
                
        except httpx.TimeoutException:
            return {
                'url': url,
                'status_code': 408,  # Request Timeout
                'error': 'Request timeout',
                'links': [],
            }
        except Exception as e:
            return {
                'url': url,
                'status_code': 0,
                'error': str(e),
                'links': [],
            }
    
    async def crawl_recursive(self, url: str, depth: int = 0) -> None:
        """Recursively crawl pages starting from the given URL."""
        # Check limits
        if depth > self.max_depth:
            return
        if len(self.visited_urls) >= self.max_pages:
            return
            
        # Normalize and check if already visited
        normalized_url = self.normalize_url(url)
        if normalized_url in self.visited_urls:
            return
            
        # Check if same domain
        if not self.is_same_domain(url):
            return
        
        # Mark as visited
        self.visited_urls.add(normalized_url)
        
        # Fetch page
        page_data = await self.fetch_page(url)
        if page_data:
            page_data['depth'] = depth
            self.pages_data.append(page_data)
            
            # Crawl linked pages
            if page_data.get('links') and depth < self.max_depth:
                # Limit concurrent requests
                tasks = []
                for link in page_data['links'][:20]:  # Limit links per page
                    if len(self.visited_urls) >= self.max_pages:
                        break
                    tasks.append(self.crawl_recursive(link, depth + 1))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
    
    async def crawl(self) -> List[Dict]:
        """Start crawling from the base URL."""
        await self.crawl_recursive(self.base_url, depth=0)
        return self.pages_data
    
    def get_statistics(self) -> Dict:
        """Get crawling statistics."""
        return {
            'total_pages': len(self.pages_data),
            'unique_urls': len(self.visited_urls),
            'max_depth_reached': max([p.get('depth', 0) for p in self.pages_data]) if self.pages_data else 0,
        }

