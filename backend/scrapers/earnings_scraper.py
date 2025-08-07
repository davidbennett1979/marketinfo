import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
from services.cache_service import CacheService
import time

logger = logging.getLogger(__name__)

class EarningsScaper:
    """
    Scraper for upcoming earnings announcements from multiple sources.
    
    Sources:
    - Yahoo Finance Earnings Calendar
    - MarketWatch Earnings Calendar
    - Investing.com Earnings Calendar
    """
    
    def __init__(self):
        self.cache = CacheService()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2  # 2 seconds between requests
    
    def _rate_limit(self):
        """Ensure we don't make requests too frequently"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    async def get_upcoming_earnings(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming earnings for the next specified days.
        
        Args:
            days_ahead: Number of days to look ahead for earnings
            
        Returns:
            List of earnings data dictionaries
        """
        cache_key = f"earnings:upcoming:{days_ahead}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached earnings data ({len(cached_data)} earnings)")
            return cached_data
        
        try:
            logger.info(f"Fetching upcoming earnings for next {days_ahead} days")
            
            # Try multiple sources and combine results
            all_earnings = []
            
            # Source 1: Yahoo Finance
            try:
                yahoo_earnings = await self._scrape_yahoo_earnings()
                all_earnings.extend(yahoo_earnings)
                logger.info(f"Got {len(yahoo_earnings)} earnings from Yahoo Finance")
            except Exception as e:
                logger.warning(f"Yahoo Finance earnings scraping failed: {str(e)}")
            
            # Source 2: MarketWatch
            try:
                marketwatch_earnings = await self._scrape_marketwatch_earnings()
                all_earnings.extend(marketwatch_earnings)
                logger.info(f"Got {len(marketwatch_earnings)} earnings from MarketWatch")
            except Exception as e:
                logger.warning(f"MarketWatch earnings scraping failed: {str(e)}")
            
            # If no real data, return mock data
            if not all_earnings:
                logger.warning("No earnings data from any source, returning mock data")
                return self._get_mock_earnings_data()
            
            # Deduplicate and filter by date
            unique_earnings = self._deduplicate_earnings(all_earnings)
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            filtered_earnings = []
            for earnings in unique_earnings:
                earnings_date = self._parse_date(earnings.get('date', ''))
                if earnings_date and earnings_date <= end_date:
                    filtered_earnings.append(earnings)
            
            # Sort by date
            filtered_earnings.sort(key=lambda x: self._parse_date(x.get('date', '')))
            
            # Cache for 2 hours
            self.cache.set(cache_key, filtered_earnings, 'default', 7200)
            
            logger.info(f"Returning {len(filtered_earnings)} upcoming earnings")
            return filtered_earnings
            
        except Exception as e:
            logger.error(f"Error in get_upcoming_earnings: {str(e)}")
            return self._get_mock_earnings_data()
    
    async def _scrape_yahoo_earnings(self) -> List[Dict[str, Any]]:
        """Scrape earnings data from Yahoo Finance earnings calendar"""
        try:
            self._rate_limit()
            
            # Yahoo Finance earnings calendar URL
            url = "https://finance.yahoo.com/calendar/earnings"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            earnings = []
            
            # Yahoo uses table structure for earnings data
            tables = soup.find_all('table')
            
            for table in tables:
                tbody = table.find('tbody')
                if not tbody:
                    continue
                
                rows = tbody.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        try:
                            company_cell = cells[0]
                            symbol_cell = cells[1]
                            date_cell = cells[2]
                            time_cell = cells[3]
                            eps_cell = cells[4] if len(cells) > 4 else None
                            
                            company = company_cell.get_text(strip=True)
                            symbol = symbol_cell.get_text(strip=True)
                            date_text = date_cell.get_text(strip=True)
                            earnings_time = time_cell.get_text(strip=True)
                            eps_estimate = eps_cell.get_text(strip=True) if eps_cell else 'N/A'
                            
                            # Skip empty or invalid data
                            if not company or not symbol or len(company) < 2:
                                continue
                            
                            # Parse earnings time
                            if 'before' in earnings_time.lower():
                                time_period = 'Before Market Open'
                            elif 'after' in earnings_time.lower():
                                time_period = 'After Market Close'
                            else:
                                time_period = 'During Market Hours'
                            
                            earnings_data = {
                                'company': company,
                                'symbol': symbol.upper(),
                                'date': date_text,
                                'time': time_period,
                                'eps_estimate': eps_estimate,
                                'source': 'Yahoo Finance'
                            }
                            
                            earnings.append(earnings_data)
                            
                        except Exception as e:
                            continue  # Skip problematic rows
            
            return earnings[:25]  # Limit to 25 earnings
            
        except Exception as e:
            logger.error(f"Error scraping Yahoo earnings: {str(e)}")
            return []
    
    async def _scrape_marketwatch_earnings(self) -> List[Dict[str, Any]]:
        """Scrape earnings data from MarketWatch earnings calendar"""
        try:
            self._rate_limit()
            
            url = "https://www.marketwatch.com/tools/earnings-calendar"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            earnings = []
            
            # MarketWatch uses various table/div structures
            tables = soup.find_all(['table', 'div'], {'class': re.compile('table|earnings|calendar', re.I)})
            
            for table in tables:
                rows = table.find_all(['tr', 'div'], recursive=True)
                
                for row in rows:
                    try:
                        # Try to extract earnings data from various row formats
                        cells = row.find_all(['td', 'div', 'span'])
                        if len(cells) >= 3:
                            
                            symbol_text = ''
                            company_text = ''
                            date_text = ''
                            time_text = ''
                            
                            # Try to extract information from cells
                            for cell in cells:
                                text = cell.get_text(strip=True)
                                
                                # Look for stock symbols (2-5 uppercase letters)
                                if re.match(r'^[A-Z]{2,5}$', text) and not symbol_text:
                                    symbol_text = text
                                
                                # Look for company names (longer text)
                                elif len(text) > 5 and text.replace(' ', '').isalnum() and not company_text:
                                    company_text = text
                                
                                # Look for dates
                                elif any(month in text for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                                    date_text = text
                                
                                # Look for time indicators
                                elif any(word in text.lower() for word in ['before', 'after', 'open', 'close']):
                                    time_text = text
                            
                            # Skip if no meaningful data
                            if not symbol_text or not company_text:
                                continue
                            
                            # Parse time
                            if 'before' in time_text.lower():
                                time_period = 'Before Market Open'
                            elif 'after' in time_text.lower():
                                time_period = 'After Market Close'
                            else:
                                time_period = 'TBD'
                            
                            earnings_data = {
                                'company': company_text,
                                'symbol': symbol_text.upper(),
                                'date': date_text or datetime.now().strftime('%Y-%m-%d'),
                                'time': time_period,
                                'eps_estimate': 'N/A',
                                'source': 'MarketWatch'
                            }
                            
                            earnings.append(earnings_data)
                    
                    except Exception as e:
                        continue  # Skip problematic rows
            
            return earnings[:20]  # Limit to 20 earnings
            
        except Exception as e:
            logger.error(f"Error scraping MarketWatch earnings: {str(e)}")
            return []
    
    def _deduplicate_earnings(self, earnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate earnings based on symbol and date"""
        seen = set()
        unique_earnings = []
        
        for earning in earnings:
            symbol = earning.get('symbol', '').upper()
            date = earning.get('date', '')
            key = f"{symbol}:{date}"
            
            if key and key not in seen and symbol:
                seen.add(key)
                unique_earnings.append(earning)
        
        return unique_earnings
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats to datetime object"""
        if not date_str:
            return datetime.now()
        
        try:
            # Common date formats
            formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%m/%d/%y',
                '%B %d, %Y',
                '%b %d, %Y',
                '%d-%m-%Y',
                '%m-%d-%Y',
                '%Y/%m/%d'
            ]
            
            # Clean the date string
            date_str = re.sub(r'[^\w\s/\-,]', '', date_str).strip()
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If no format matches, return today
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {str(e)}")
            return datetime.now()
    
    def _get_mock_earnings_data(self) -> List[Dict[str, Any]]:
        """Return mock earnings data when scraping fails"""
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        
        return [
            {
                'company': 'Apple Inc.',
                'symbol': 'AAPL',
                'date': today.strftime('%Y-%m-%d'),
                'time': 'After Market Close',
                'eps_estimate': '$1.95',
                'source': 'Mock Data'
            },
            {
                'company': 'Microsoft Corporation',
                'symbol': 'MSFT',
                'date': today.strftime('%Y-%m-%d'),
                'time': 'After Market Close',
                'eps_estimate': '$2.65',
                'source': 'Mock Data'
            },
            {
                'company': 'Tesla Inc.',
                'symbol': 'TSLA',
                'date': tomorrow.strftime('%Y-%m-%d'),
                'time': 'After Market Close',
                'eps_estimate': '$0.85',
                'source': 'Mock Data'
            },
            {
                'company': 'Amazon.com Inc.',
                'symbol': 'AMZN',
                'date': tomorrow.strftime('%Y-%m-%d'),
                'time': 'After Market Close',
                'eps_estimate': '$0.50',
                'source': 'Mock Data'
            },
            {
                'company': 'Meta Platforms Inc.',
                'symbol': 'META',
                'date': day_after.strftime('%Y-%m-%d'),
                'time': 'After Market Close',
                'eps_estimate': '$3.25',
                'source': 'Mock Data'
            },
            {
                'company': 'Alphabet Inc.',
                'symbol': 'GOOGL',
                'date': day_after.strftime('%Y-%m-%d'),
                'time': 'After Market Close',
                'eps_estimate': '$1.45',
                'source': 'Mock Data'
            }
        ]
    
    async def get_earnings_for_date(self, target_date: str) -> List[Dict[str, Any]]:
        """Get earnings for a specific date"""
        try:
            all_earnings = await self.get_upcoming_earnings(7)
            date_earnings = [
                earning for earning in all_earnings 
                if earning.get('date', '').startswith(target_date)
            ]
            return date_earnings
        except Exception as e:
            logger.error(f"Error getting earnings for date {target_date}: {str(e)}")
            return []