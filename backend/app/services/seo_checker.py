import httpx
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.core.config import settings


class SEOCheckerService:
    """Service for checking SEO-related issues."""
    
    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT
    
    def check_favicon(self, html_content: str, base_url: str) -> Dict:
        """
        Check if favicon is present.
        
        Checks for:
        - <link rel="icon">
        - <link rel="shortcut icon">
        - /favicon.ico
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Check for favicon link in HTML
        favicon_links = soup.find_all('link', rel=lambda x: x and 'icon' in x.lower())
        
        if favicon_links:
            return {
                'has_favicon': True,
                'favicon_url': urljoin(base_url, favicon_links[0].get('href', '')),
                'method': 'HTML link tag',
            }
        
        # Will check /favicon.ico separately
        return {
            'has_favicon': False,
            'favicon_url': None,
            'method': None,
        }
    
    async def check_favicon_file(self, base_url: str) -> bool:
        """Check if /favicon.ico exists."""
        parsed = urlparse(base_url)
        favicon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.head(favicon_url)
                return response.status_code == 200
        except Exception:
            return False
    
    async def check_robots_txt(self, base_url: str) -> Dict:
        """
        Check robots.txt file.
        
        Checks:
        - If file exists
        - If site is open for robots (not completely disallowed)
        """
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(robots_url)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Check if all robots are disallowed
                    is_blocked = 'User-agent: *' in content and 'Disallow: /' in content
                    
                    # Check for sitemap
                    has_sitemap = 'Sitemap:' in content
                    
                    return {
                        'exists': True,
                        'url': robots_url,
                        'is_blocked_for_robots': is_blocked,
                        'has_sitemap': has_sitemap,
                        'content': content[:500],  # First 500 chars
                    }
                else:
                    return {
                        'exists': False,
                        'url': robots_url,
                        'status_code': response.status_code,
                    }
        except Exception as e:
            return {
                'exists': False,
                'url': robots_url,
                'error': str(e),
            }
    
    def check_meta_tags(self, html_content: str) -> Dict:
        """
        Check important meta tags.
        
        Checks for:
        - <title>
        - meta description
        - meta keywords
        - Open Graph tags
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Title
        title_tag = soup.find('title')
        title = title_tag.string.strip() if title_tag and title_tag.string else None
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'] if meta_desc and meta_desc.get('content') else None
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords = meta_keywords['content'] if meta_keywords and meta_keywords.get('content') else None
        
        # Open Graph
        og_title = soup.find('meta', property='og:title')
        og_description = soup.find('meta', property='og:description')
        og_image = soup.find('meta', property='og:image')
        
        # Viewport (mobile-friendly)
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        
        # Charset
        charset = soup.find('meta', charset=True) or soup.find('meta', attrs={'http-equiv': 'Content-Type'})
        
        return {
            'title': title,
            'title_length': len(title) if title else 0,
            'description': description,
            'description_length': len(description) if description else 0,
            'keywords': keywords,
            'has_og_tags': bool(og_title or og_description or og_image),
            'has_viewport': bool(viewport),
            'has_charset': bool(charset),
        }
    
    async def check_page(self, html_content: str, base_url: str) -> List[Dict]:
        """
        Run all SEO checks and return list of issues.
        """
        errors = []
        
        # Check favicon
        favicon_result = self.check_favicon(html_content, base_url)
        if not favicon_result['has_favicon']:
            # Check /favicon.ico
            has_favicon_file = await self.check_favicon_file(base_url)
            if not has_favicon_file:
                errors.append({
                    'message': 'Відсутній favicon',
                    'suggestion': 'Додайте <link rel="icon" href="/favicon.ico"> у <head> або розмістіть файл /favicon.ico',
                    'severity': 'warning',
                })
        
        # Check meta tags
        meta = self.check_meta_tags(html_content)
        
        if not meta['title']:
            errors.append({
                'message': 'Відсутній тег <title>',
                'suggestion': 'Додайте <title>Назва сторінки</title> у <head>',
                'severity': 'error',
            })
        elif meta['title_length'] < 30:
            errors.append({
                'message': f'Занадто короткий title ({meta["title_length"]} символів)',
                'suggestion': 'Рекомендована довжина: 30-60 символів',
                'severity': 'warning',
            })
        elif meta['title_length'] > 60:
            errors.append({
                'message': f'Занадто довгий title ({meta["title_length"]} символів)',
                'suggestion': 'Рекомендована довжина: 30-60 символів',
                'severity': 'warning',
            })
        
        if not meta['description']:
            errors.append({
                'message': 'Відсутній meta description',
                'suggestion': 'Додайте <meta name="description" content="Опис сторінки">',
                'severity': 'warning',
            })
        elif meta['description_length'] < 50:
            errors.append({
                'message': f'Занадто короткий meta description ({meta["description_length"]} символів)',
                'suggestion': 'Рекомендована довжина: 120-160 символів',
                'severity': 'info',
            })
        elif meta['description_length'] > 160:
            errors.append({
                'message': f'Занадто довгий meta description ({meta["description_length"]} символів)',
                'suggestion': 'Рекомендована довжина: 120-160 символів',
                'severity': 'info',
            })
        
        if not meta['has_viewport']:
            errors.append({
                'message': 'Відсутній meta viewport (не оптимізовано для мобільних)',
                'suggestion': 'Додайте <meta name="viewport" content="width=device-width, initial-scale=1.0">',
                'severity': 'warning',
            })
        
        if not meta['has_charset']:
            errors.append({
                'message': 'Відсутнє визначення кодування (charset)',
                'suggestion': 'Додайте <meta charset="UTF-8">',
                'severity': 'warning',
            })
        
        return errors
    
    async def check_robots_accessibility(self, base_url: str) -> Optional[Dict]:
        """Check if site is accessible for robots."""
        robots_result = await self.check_robots_txt(base_url)
        
        if not robots_result.get('exists'):
            return {
                'message': 'Файл robots.txt не знайдено',
                'suggestion': 'Створіть файл robots.txt для контролю індексації',
                'severity': 'info',
            }
        
        if robots_result.get('is_blocked_for_robots'):
            return {
                'message': 'Сайт заблокований для всіх роботів (Disallow: /)',
                'suggestion': 'Перевірте robots.txt - можливо, сайт не буде індексуватися пошуковими системами',
                'severity': 'critical',
            }
        
        return None

