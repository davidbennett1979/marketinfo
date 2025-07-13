from typing import List, Dict, Any
from datetime import datetime
import logging
from scrapers.base_scraper import BaseScraper
import feedparser

logger = logging.getLogger(__name__)

class NewsScraperRSS:
    """
    News scraper using RSS feeds (no HTML scraping needed).
    More reliable and faster than web scraping.
    """
    
    def __init__(self):
        self.rss_feeds = {
            'marketwatch': 'http://feeds.marketwatch.com/marketwatch/topstories/',
            'reuters': 'https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best',
            'cnbc': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114',
            'yahoo': 'https://finance.yahoo.com/news/rssindex',
            'bloomberg': 'https://feeds.bloomberg.com/markets/news.rss'
        }
    
    def scrape_all_feeds(self) -> List[Dict[str, Any]]:
        """Scrape all RSS feeds and return combined results"""
        all_articles = []
        
        for source, url in self.rss_feeds.items():
            try:
                articles = self.scrape_feed(source, url)
                all_articles.extend(articles)
                logger.info(f"Scraped {len(articles)} articles from {source}")
            except Exception as e:
                logger.error(f"Error scraping {source}: {str(e)}")
        
        # Sort by published date (newest first)
        all_articles.sort(key=lambda x: x['published_at'], reverse=True)
        
        return all_articles
    
    def scrape_feed(self, source: str, url: str) -> List[Dict[str, Any]]:
        """Scrape a single RSS feed"""
        try:
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries[:20]:  # Limit to 20 articles per source
                article = {
                    'title': entry.get('title', ''),
                    'source': source.upper(),
                    'url': entry.get('link', ''),
                    'description': entry.get('summary', ''),
                    'published_at': self._parse_date(entry.get('published', '')),
                    'author': entry.get('author', ''),
                    'tags': [tag.term for tag in entry.get('tags', [])]
                }
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing feed {url}: {str(e)}")
            return []
    
    def _parse_date(self, date_string: str) -> str:
        """Parse various date formats to ISO format"""
        try:
            # feedparser returns a time struct
            if hasattr(date_string, 'tm_year'):
                return datetime(*date_string[:6]).isoformat()
            else:
                # Try to parse string format
                from dateutil import parser
                return parser.parse(date_string).isoformat()
        except:
            # Return current time if parsing fails
            return datetime.now().isoformat()


class EarningsCalendarScraper(BaseScraper):
    """Scraper for earnings calendar data"""
    
    def __init__(self):
        super().__init__("https://www.marketwatch.com", rate_limit=2.0)
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape earnings calendar for today and this week"""
        earnings_data = []
        
        # MarketWatch earnings calendar URL
        url = f"{self.base_url}/tools/earnings-calendar"
        
        html = self.fetch_page(url)
        if not html:
            logger.error("Failed to fetch earnings calendar")
            return earnings_data
        
        soup = self.parse_html(html)
        
        # Find earnings table (this is a simplified example)
        # In reality, you'd need to inspect the actual HTML structure
        earnings_table = soup.find('table', {'class': 'earnings-table'})
        
        if not earnings_table:
            # Try alternative selectors
            earnings_table = soup.find('div', {'class': 'element--table'})
        
        if earnings_table:
            rows = earnings_table.find_all('tr')[1:]  # Skip header
            
            for row in rows[:50]:  # Limit to 50 companies
                cells = row.find_all('td')
                if len(cells) >= 4:
                    earnings_data.append({
                        'symbol': cells[0].text.strip(),
                        'company_name': cells[1].text.strip(),
                        'earnings_date': datetime.now().strftime('%Y-%m-%d'),
                        'earnings_time': cells[2].text.strip(),
                        'estimated_eps': cells[3].text.strip()
                    })
        
        return earnings_data


class ShortInterestScraper(BaseScraper):
    """Scraper for short interest data"""
    
    def __init__(self):
        super().__init__("https://www.highshortinterest.com", rate_limit=2.0)
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape high short interest stocks"""
        short_data = []
        
        html = self.fetch_page(self.base_url)
        if not html:
            logger.error("Failed to fetch short interest data")
            return short_data
        
        soup = self.parse_html(html)
        
        # Find the main table (this is a simplified example)
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows[:30]:  # Top 30 high short interest stocks
                cells = row.find_all('td')
                if len(cells) >= 3:
                    short_data.append({
                        'symbol': cells[0].text.strip(),
                        'company_name': cells[1].text.strip(),
                        'short_interest_percent': cells[2].text.strip(),
                        'updated_at': datetime.now().isoformat()
                    })
        
        return short_data