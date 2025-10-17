import httpx
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from app.core.config import settings


class LinkCheckerService:
    """Service for checking broken links and phone numbers."""
    
    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT
        self.checked_links = {}  # Cache for already checked links
    
    async def check_link(self, url: str) -> Dict:
        """
        Check if a link is accessible.
        
        Returns dict with status_code and error message if any.
        """
        # Return cached result if available
        if url in self.checked_links:
            return self.checked_links[url]
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.head(url)
                result = {
                    'url': url,
                    'status_code': response.status_code,
                    'is_broken': response.status_code >= 400,
                    'error': None,
                }
        except httpx.TimeoutException:
            result = {
                'url': url,
                'status_code': 408,
                'is_broken': True,
                'error': 'Request timeout',
            }
        except httpx.ConnectError:
            result = {
                'url': url,
                'status_code': 0,
                'is_broken': True,
                'error': 'Connection failed',
            }
        except Exception as e:
            result = {
                'url': url,
                'status_code': 0,
                'is_broken': True,
                'error': str(e),
            }
        
        # Cache result
        self.checked_links[url] = result
        return result
    
    async def check_all_links(self, html_content: str, base_url: str) -> List[Dict]:
        """
        Extract and check all links from HTML content.
        
        Returns list of broken links with details.
        """
        soup = BeautifulSoup(html_content, 'lxml')
        links = soup.find_all('a', href=True)
        
        errors = []
        
        for link in links:
            href = link['href']
            
            # Skip anchors, javascript, mailto, etc.
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Check link
            result = await self.check_link(absolute_url)
            
            if result['is_broken']:
                # Get link text and context
                link_text = link.get_text(strip=True)
                
                error = {
                    'link_url': absolute_url,
                    'link_text': link_text,
                    'status_code': result['status_code'],
                    'error': result['error'],
                    'message': f"Битое посилання: {absolute_url} (HTTP {result['status_code']})",
                }
                errors.append(error)
        
        return errors
    
    def extract_phone_numbers(self, html_content: str) -> List[Dict]:
        """
        Extract phone numbers from HTML (tel: links).
        
        Returns list of phone numbers with validation.
        """
        soup = BeautifulSoup(html_content, 'lxml')
        phone_links = soup.find_all('a', href=re.compile(r'^tel:'))
        
        phones = []
        
        for link in phone_links:
            href = link['href']
            phone_number = href.replace('tel:', '').strip()
            link_text = link.get_text(strip=True)
            
            phones.append({
                'href': href,
                'phone_number': phone_number,
                'link_text': link_text,
            })
        
        return phones
    
    def validate_ukrainian_phone(self, phone: str) -> Dict:
        """
        Validate Ukrainian phone number format.
        
        Ukrainian formats:
        - +380XXXXXXXXX (13 chars)
        - 380XXXXXXXXX (12 chars)
        - 0XXXXXXXXX (10 chars)
        """
        # Clean phone number
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Check formats
        patterns = [
            (r'^\+380\d{9}$', 'Правильний формат: +380XXXXXXXXX'),
            (r'^380\d{9}$', 'Правильний формат, але краще з +: +380XXXXXXXXX'),
            (r'^0\d{9}$', 'Локальний формат, додайте код країни: +380XXXXXXXXX'),
        ]
        
        for pattern, message in patterns:
            if re.match(pattern, cleaned):
                return {
                    'is_valid': True,
                    'format': message,
                    'cleaned': cleaned,
                }
        
        return {
            'is_valid': False,
            'format': None,
            'cleaned': cleaned,
            'error': 'Неправильний формат українського номеру телефону',
        }
    
    def check_phone_numbers(self, html_content: str) -> List[Dict]:
        """
        Check all phone numbers in HTML for correct format and clickability.
        
        Returns list of errors.
        """
        errors = []
        phones = self.extract_phone_numbers(html_content)
        
        for phone_data in phones:
            validation = self.validate_ukrainian_phone(phone_data['phone_number'])
            
            if not validation['is_valid']:
                error = {
                    'phone_number': phone_data['phone_number'],
                    'link_text': phone_data['link_text'],
                    'href': phone_data['href'],
                    'message': validation['error'],
                    'suggestion': '+380XXXXXXXXX',
                }
                errors.append(error)
        
        # Also check for phone numbers in plain text (not clickable)
        soup = BeautifulSoup(html_content, 'lxml')
        text = soup.get_text()
        
        # Find phone-like patterns in text
        phone_patterns = [
            r'\+?\d{3}[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
            r'\+?\d{3}[\s\-]?\d{9}',
            r'0\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
        ]
        
        for pattern in phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                phone_text = match.group(0)
                
                # Check if this phone is already in a tel: link
                is_clickable = any(p['link_text'] in phone_text or phone_text in p['link_text'] 
                                  for p in phones)
                
                if not is_clickable:
                    # Get context
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]
                    
                    error = {
                        'phone_number': phone_text,
                        'context': context,
                        'message': f'Номер телефону не є клікабельним: {phone_text}',
                        'suggestion': f'Зробіть посилання: <a href="tel:{phone_text}">{phone_text}</a>',
                    }
                    errors.append(error)
        
        return errors

