import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
from services.cache_service import CacheService
from services.alpha_vantage_service import AlphaVantageService
import time

logger = logging.getLogger(__name__)

class IPOScraper:
    """
    Scraper for upcoming IPO information from multiple reliable sources.
    
    Sources:
    - MarketWatch IPO Calendar
    - Yahoo Finance IPO Calendar  
    - Investing.com IPO Calendar
    """
    
    def __init__(self):
        self.cache = CacheService()
        self.alpha_vantage = AlphaVantageService()
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
    
    async def get_upcoming_ipos(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Get upcoming IPOs for the next specified days.
        
        Args:
            days_ahead: Number of days to look ahead for IPOs
            
        Returns:
            List of IPO data dictionaries
        """
        cache_key = f"ipos:upcoming:{days_ahead}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached IPO data ({len(cached_data)} IPOs)")
            return cached_data
        
        try:
            logger.info(f"Fetching upcoming IPOs for next {days_ahead} days")
            
            # Try multiple sources and combine results
            all_ipos = []
            
            # Source 1: Alpha Vantage API (primary source)
            try:
                alpha_vantage_ipos = await self.alpha_vantage.get_ipo_calendar(days_ahead)
                
                # Convert Alpha Vantage format to our standard format
                for ipo in alpha_vantage_ipos:
                    all_ipos.append({
                        'company': ipo.get('company_name', ipo.get('company')),
                        'symbol': ipo.get('symbol', 'TBD'),
                        'date': ipo.get('expected_date', ipo.get('date')),
                        'price_range': f"${ipo.get('price_range_low', 0):.2f}-${ipo.get('price_range_high', 0):.2f}" if ipo.get('price_range_low') else ipo.get('price_range', 'TBD'),
                        'shares': f"{ipo.get('shares_offered', 0)/1000000:.1f}M" if ipo.get('shares_offered') else 'N/A',
                        'market_cap': f"${ipo.get('dollar_value_offered', 0)/1000000000:.1f}B" if ipo.get('dollar_value_offered') else 'N/A',
                        'lead_underwriter': ', '.join(ipo.get('lead_underwriters', [])) if ipo.get('lead_underwriters') else 'N/A',
                        'exchange': ipo.get('exchange', 'N/A'),
                        'sector': ipo.get('sector', 'N/A'),
                        'industry': ipo.get('industry', 'N/A'),
                        'status': ipo.get('status', 'Expected'),
                        'source': 'Alpha Vantage'
                    })
                logger.info(f"Got {len(alpha_vantage_ipos)} IPOs from Alpha Vantage")
                
                # If we have good data from Alpha Vantage, we can skip other sources
                if len(alpha_vantage_ipos) >= 3:
                    # Cache and return early
                    self.cache.set(cache_key, all_ipos, 'default', 21600)  # 6 hours
                    logger.info(f"Returning {len(all_ipos)} IPOs from Alpha Vantage (cached)")
                    return all_ipos
                    
            except Exception as e:
                logger.warning(f"Alpha Vantage IPO fetch failed: {str(e)}")
            
            # Source 2: MarketWatch (fallback)
            if len(all_ipos) < 3:
                try:
                    marketwatch_ipos = await self._scrape_marketwatch_ipos()
                    all_ipos.extend(marketwatch_ipos)
                    logger.info(f"Got {len(marketwatch_ipos)} IPOs from MarketWatch")
                except Exception as e:
                    logger.warning(f"MarketWatch IPO scraping failed: {str(e)}")
            
            # Source 3: Yahoo Finance (additional fallback)
            if len(all_ipos) < 3:
                try:
                    yahoo_ipos = await self._scrape_yahoo_ipos()
                    all_ipos.extend(yahoo_ipos)
                    logger.info(f"Got {len(yahoo_ipos)} IPOs from Yahoo Finance")
                except Exception as e:
                    logger.warning(f"Yahoo Finance IPO scraping failed: {str(e)}")
            
            # If no real data, return empty list
            if not all_ipos:
                logger.warning("No IPO data from any source")
                return []
            
            # Deduplicate and filter by date
            unique_ipos = self._deduplicate_ipos(all_ipos)
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            filtered_ipos = []
            for ipo in unique_ipos:
                ipo_date = self._parse_date(ipo.get('date', ''))
                if ipo_date and ipo_date <= end_date:
                    filtered_ipos.append(ipo)
            
            # Sort by date
            filtered_ipos.sort(key=lambda x: self._parse_date(x.get('date', '')))
            
            # Cache for 4 hours
            self.cache.set(cache_key, filtered_ipos, 'default', 14400)
            
            logger.info(f"Returning {len(filtered_ipos)} upcoming IPOs")
            return filtered_ipos
            
        except Exception as e:
            logger.error(f"Error in get_upcoming_ipos: {str(e)}")
            return []
    
    
    async def _fetch_fmp_ipos(self) -> List[Dict[str, Any]]:
        """Try Financial Modeling Prep API for IPO calendar (has free tier)"""
        try:
            # FMP has a free tier with IPO calendar
            # But for now, let's try a simpler RSS-based approach
            return await self._fetch_rss_ipo_data()
            
        except Exception as e:
            logger.error(f"Error fetching FMP IPOs: {str(e)}")
            return []
    
    async def _fetch_rss_ipo_data(self) -> List[Dict[str, Any]]:
        """Try to get IPO data from RSS feeds or simpler sources"""
        try:
            # No RSS IPO feeds available - return empty array
            # Real IPO data should come from API sources
            return []
            
        except Exception as e:
            logger.error(f"Error fetching RSS IPO data: {str(e)}")
            return []
    
    async def _scrape_marketwatch_ipos(self) -> List[Dict[str, Any]]:
        """Scrape IPO data from MarketWatch IPO calendar"""
        try:
            self._rate_limit()
            
            # Try a simpler approach - MarketWatch RSS or simpler pages
            url = "https://www.marketwatch.com/tools/ipo-calendar"
            
            # Enhanced headers to appear more like a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(url, headers=headers, timeout=15)
            
            # If blocked, try alternative approach
            if response.status_code in [403, 401, 429]:
                logger.warning(f"MarketWatch blocked request with status {response.status_code}")
                return []
            
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            ipos = []
            
            # Look for IPO data in various formats
            # Try to find any text that looks like IPO data
            text_content = soup.get_text()
            
            # Look for company names followed by ticker symbols
            # Pattern: Company Name (TICKER) Date Price
            ipo_patterns = re.findall(r'([A-Za-z\s&\.]+)\s*\(([A-Z]{2,5})\)\s*([0-9\/\-]+)\s*\$?([0-9\-\$\.]+)', text_content)
            
            for match in ipo_patterns:
                company, symbol, date, price_info = match
                company = company.strip()
                
                # Skip if company name is too short or generic
                if len(company) < 3 or company.lower() in ['ipo', 'stock', 'share']:
                    continue
                
                ipo_data = {
                    'company': company,
                    'symbol': symbol,
                    'date': date,
                    'price_range': f"${price_info}" if not price_info.startswith('$') else price_info,
                    'shares': 'N/A',
                    'market_cap': 'N/A',
                    'source': 'MarketWatch'
                }
                
                ipos.append(ipo_data)
                if len(ipos) >= 10:  # Limit results
                    break
            
            return ipos
            
        except Exception as e:
            logger.error(f"Error scraping MarketWatch IPOs: {str(e)}")
            return []
    
    async def _scrape_yahoo_ipos(self) -> List[Dict[str, Any]]:
        """Scrape IPO data from Yahoo Finance IPO calendar"""
        try:
            self._rate_limit()
            
            url = "https://finance.yahoo.com/calendar/ipo"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            ipos = []
            
            # Yahoo uses table structure for IPO data
            tables = soup.find_all('table')
            
            for table in tables:
                tbody = table.find('tbody')
                if not tbody:
                    continue
                    
                rows = tbody.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        try:
                            company = cells[0].get_text(strip=True)
                            symbol = cells[1].get_text(strip=True)
                            date_text = cells[2].get_text(strip=True)
                            price_range = cells[3].get_text(strip=True)
                            
                            # Skip empty or invalid data
                            if not company or len(company) < 2:
                                continue
                                
                            ipo_data = {
                                'company': company,
                                'symbol': symbol if symbol and symbol != '-' else 'TBD',
                                'date': date_text,
                                'price_range': price_range if price_range and price_range != '-' else 'N/A',
                                'shares': 'N/A',
                                'market_cap': 'N/A',
                                'source': 'Yahoo Finance'
                            }
                            
                            ipos.append(ipo_data)
                            
                        except Exception as e:
                            continue  # Skip problematic rows
            
            return ipos[:15]  # Limit to 15 IPOs
            
        except Exception as e:
            logger.error(f"Error scraping Yahoo IPOs: {str(e)}")
            return []
    
    def _deduplicate_ipos(self, ipos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate IPOs based on company name"""
        seen = set()
        unique_ipos = []
        
        for ipo in ipos:
            company = ipo.get('company', '').lower().strip()
            if company and company not in seen and len(company) > 2:
                seen.add(company)
                unique_ipos.append(ipo)
        
        return unique_ipos
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats to datetime object"""
        if not date_str or date_str.lower() in ['tbd', 'n/a', 'pending', '-', '']:
            return None
        
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
            
            # If no format matches, return None for TBD dates
            return None
            
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {str(e)}")
            return None
    
    
    async def get_recent_ipos(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get recently completed IPOs with performance tracking"""
        cache_key = f"ipos:recent:{days_back}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Try to fetch real recent IPO data from Alpha Vantage if available
            alpha_vantage = AlphaVantageService()
            recent_ipos = await alpha_vantage.get_ipo_calendar(days_ahead=0)  # Get recent IPOs
            
            if recent_ipos:
                # Filter for recent IPOs within days_back period
                start_date = datetime.now() - timedelta(days=days_back)
                filtered_ipos = []
                
                for ipo in recent_ipos:
                    ipo_date = self._parse_date(ipo.get('date', ''))
                    if ipo_date and ipo_date >= start_date.date():
                        filtered_ipos.append(ipo)
                
                # Cache for 6 hours
                if filtered_ipos:
                    self.cache.set(cache_key, filtered_ipos, 'default', 21600)
                    return filtered_ipos
            
            # No recent IPO data available
            return []
            
        except Exception as e:
            logger.error(f"Error fetching recent IPOs: {str(e)}")
            return []