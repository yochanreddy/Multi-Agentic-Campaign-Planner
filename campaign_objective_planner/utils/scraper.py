import requests
from bs4 import BeautifulSoup
from typing import Dict
from urllib.parse import urlparse
import logging
import traceback

logger = logging.getLogger(__name__)

class URLScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

    def _extract_useful_content(self, soup: BeautifulSoup) -> str:
        """
        Extract useful content from the parsed HTML.
        Focuses on elements that would help determine campaign objectives.
        """
        content_parts = []
        
        # Extract title
        if soup.title:
            content_parts.append(f"Title: {soup.title.string.strip()}")
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content_parts.append(f"Description: {meta_desc['content'].strip()}")
        
        # Extract main content
        main_content = []
        
        # Look for main content areas
        for tag in ['main', 'article', 'div[role="main"]']:
            elements = soup.select(tag)
            for element in elements:
                # Get text from headings
                headings = element.find_all(['h1', 'h2', 'h3'])
                for heading in headings:
                    if heading.text.strip():
                        main_content.append(f"Heading: {heading.text.strip()}")
                
                # Get text from paragraphs
                paragraphs = element.find_all('p')
                for p in paragraphs:
                    if p.text.strip():
                        main_content.append(p.text.strip())
        
        # If no main content found, try to get any meaningful text
        if not main_content:
            # Get text from any headings
            headings = soup.find_all(['h1', 'h2', 'h3'])
            for heading in headings:
                if heading.text.strip():
                    main_content.append(f"Heading: {heading.text.strip()}")
            
            # Get text from any paragraphs
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                if p.text.strip():
                    main_content.append(p.text.strip())
        
        content_parts.extend(main_content)
        
        # Join all content parts
        content = "\n".join(content_parts)
        
        # Truncate if needed (using ~20K tokens)
        if len(content) > 20000:
            content = content[:20000] + "..."
            
        return content

    def scrape(self, url: str) -> Dict[str, str]:
        """
        Scrape a URL and return useful content for objective determination.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary containing:
            - content: Extracted useful content
            - error: Error message if any
        """
        try:
            # Ensure URL has scheme
            if not urlparse(url).scheme:
                url = 'https://' + url
            
            logger.info(f"Scraping website: {url}")
            
            # Add timeout and verify SSL
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=10,
                verify=True,
                allow_redirects=True
            )
            response.raise_for_status()
            
            logger.info(f"Successfully fetched website content. Status code: {response.status_code}")
            
            # Parse HTML and extract useful content
            soup = BeautifulSoup(response.text, 'html.parser')
            content = self._extract_useful_content(soup)
            
            logger.info(f"Extracted content length: {len(content)}")
            
            return {
                'content': content,
                'error': None
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout error scraping website {url}")
            return {
                'content': '',
                'error': "Request timed out. The website might be blocking automated access."
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error scraping website {url}: {str(e)}")
            return {
                'content': '',
                'error': f"Request error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error scraping website {url}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'content': '',
                'error': f"General error: {str(e)}"
            } 