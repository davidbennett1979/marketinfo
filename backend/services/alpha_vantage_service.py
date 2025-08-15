"""
Alpha Vantage API Service for Financial Data

This service provides integration with Alpha Vantage API to fetch:
- Earnings calendar data
- IPO calendar data  
- Company overview and fundamentals

Alpha Vantage offers a free tier with 5 API requests per minute and 500 requests per day.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
import asyncio
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

class AlphaVantageService:
    """Service for fetching financial data from Alpha Vantage API"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = 'https://www.alphavantage.co/query'
        self.cache = CacheService()
        self.request_count = 0
        self.last_request_time = datetime.now()
        
    async def _rate_limit(self):
        """Ensure we don't exceed 5 requests per minute"""
        self.request_count += 1
        current_time = datetime.now()
        
        # Reset counter if more than a minute has passed
        if (current_time - self.last_request_time).seconds >= 60:
            self.request_count = 1
            self.last_request_time = current_time
        
        # If we've made 5 requests, wait until the minute is up
        if self.request_count >= 5:
            wait_time = 60 - (current_time - self.last_request_time).seconds
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time} seconds")
                await asyncio.sleep(wait_time)
                self.request_count = 1
                self.last_request_time = datetime.now()
    
    async def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make API request with rate limiting and error handling"""
        await self._rate_limit()
        
        params['apikey'] = self.api_key
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=30.0)
                response.raise_for_status()
                
                # Check if response is JSON or CSV
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    data = response.json()
                    
                    # Check for API errors
                    if 'Error Message' in data:
                        logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                        return {}
                        
                    if 'Note' in data:
                        logger.warning(f"Alpha Vantage API note: {data['Note']}")
                        return {}
                        
                    return data
                else:
                    # Return raw text for CSV responses
                    return response.text
                
        except Exception as e:
            logger.error(f"Error making Alpha Vantage API request: {str(e)}")
            return {}
    
    async def get_earnings_calendar(self) -> List[Dict[str, Any]]:
        """
        Get earnings calendar data from Alpha Vantage
        
        Returns:
            List of earnings announcements with company details
        """
        cache_key = "alpha_vantage:earnings_calendar"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached earnings data ({len(cached_data)} items)")
            return cached_data
        
        try:
            # Alpha Vantage earnings calendar endpoint
            params = {
                'function': 'EARNINGS_CALENDAR',
                'horizon': '3month'  # Get earnings for next 3 months
            }
            
            data = await self._make_request(params)
            
            if not data:
                logger.warning("No earnings data from Alpha Vantage")
                return []
            
            # Parse CSV response (Alpha Vantage returns CSV for earnings calendar)
            earnings_list = []
            if isinstance(data, str):
                lines = data.strip().split('\n')
                if len(lines) > 1:
                    # Parse CSV header
                    import csv
                    from io import StringIO
                    
                    csv_reader = csv.DictReader(StringIO(data))
                    for row in csv_reader:
                        # Only include companies with actual estimates
                        if row.get('estimate') and row.get('estimate').strip():
                            earnings_list.append({
                                'company': row.get('name', 'Unknown'),
                                'symbol': row.get('symbol', 'N/A'),
                                'date': row.get('reportDate', datetime.now().strftime('%Y-%m-%d')),
                                'time': 'TBD',  # Alpha Vantage doesn't provide time
                                'eps_estimate': f"${row.get('estimate', 'N/A')}",
                                'eps_prior': 'N/A',  # Not provided in the response
                                'source': 'Alpha Vantage'
                            })
            
            # If we got data, cache it for 4 hours
            if earnings_list:
                self.cache.set(cache_key, earnings_list, 'default', 14400)
                logger.info(f"Cached {len(earnings_list)} earnings from Alpha Vantage")
            else:
                # No data available from API
                earnings_list = []
            
            return earnings_list
            
        except Exception as e:
            logger.error(f"Error fetching earnings calendar: {str(e)}")
            return []
    
    async def get_ipo_calendar(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Get IPO calendar data from Alpha Vantage API.
        """
        cache_key = f"alpha_vantage:ipo_calendar:{days_ahead}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached IPO data ({len(cached_data)} items)")
            return cached_data
        
        try:
            # Alpha Vantage IPO calendar endpoint
            params = {
                'function': 'IPO_CALENDAR'
            }
            
            data = await self._make_request(params)
            
            if not data:
                logger.warning("No IPO data from Alpha Vantage API")
                return []
            
            # Parse CSV response (Alpha Vantage returns CSV for IPO calendar)
            ipo_list = []
            if isinstance(data, str):
                import csv
                from io import StringIO
                
                csv_reader = csv.DictReader(StringIO(data))
                for row in csv_reader:
                    # Convert to our standard format
                    ipo_list.append({
                        'company': row.get('name', 'Unknown'),
                        'symbol': row.get('symbol', 'TBD'),
                        'date': row.get('ipoDate', datetime.now().strftime('%Y-%m-%d')),
                        'price_range': f"${row.get('priceRangeLow', '0')}-${row.get('priceRangeHigh', '0')}",
                        'shares': 'N/A',  # Not provided in response
                        'market_cap': 'N/A',  # Not provided in response
                        'exchange': row.get('exchange', 'N/A'),
                        'currency': row.get('currency', 'USD'),
                        'source': 'Alpha Vantage'
                    })
            
            # If we got data, cache it for 12 hours
            if ipo_list:
                self.cache.set(cache_key, ipo_list, 'default', 43200)
                logger.info(f"Cached {len(ipo_list)} IPOs from Alpha Vantage")
            
            return ipo_list
            
        except Exception as e:
            logger.error(f"Error generating IPO data: {str(e)}")
            return []
    
    async def _fetch_polygon_ipos(self) -> List[Dict[str, Any]]:
        """Try to fetch IPO data from Polygon.io free tier"""
        try:
            # Polygon.io has a generous free tier
            # No IPO data available from Polygon free tier
            # In production, you would register for a free Polygon.io API key
            return []
            
        except Exception as e:
            logger.error(f"Error fetching Polygon IPOs: {str(e)}")
            return []
    
    async def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Get company overview data for a specific symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Company overview data including fundamentals
        """
        cache_key = f"alpha_vantage:overview:{symbol}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol
            }
            
            data = await self._make_request(params)
            
            if data:
                # Cache for 24 hours
                self.cache.set(cache_key, data, 'default', 86400)
                
            return data
            
        except Exception as e:
            logger.error(f"Error fetching company overview for {symbol}: {str(e)}")
            return {}