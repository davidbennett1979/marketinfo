import time
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import httpx
from bs4 import BeautifulSoup
import random

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """
    Base class for all web scrapers.
    Provides common functionality like rate limiting, retries, and user agents.
    """
    
    def __init__(self, base_url: str, rate_limit: float = 1.0):
        """
        Initialize the base scraper.
        
        Args:
            base_url: The base URL for the website to scrape
            rate_limit: Minimum seconds between requests (default: 1.0)
        """
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = httpx.Client(timeout=30.0)
        
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
    
    def _get_headers(self) -> Dict[str, str]:
        """Get randomized headers for requests"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def _rate_limit_wait(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """
        Fetch a web page with retries and rate limiting.
        
        Args:
            url: The URL to fetch
            retries: Number of retry attempts
            
        Returns:
            The page HTML content or None if failed
        """
        for attempt in range(retries):
            try:
                self._rate_limit_wait()
                
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:  # Too Many Requests
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP {response.status_code} for {url}")
                    
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html, 'html.parser')
    
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method to be implemented by subclasses.
        Should return a list of scraped items.
        """
        pass
    
    def close(self):
        """Close the HTTP session"""
        self.session.close()