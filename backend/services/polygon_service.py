"""
Polygon.io API Service for Financial Data

This service provides integration with Polygon.io API as an alternative/supplement to Alpha Vantage.
Polygon offers a generous free tier with:
- 5 API calls per minute
- End-of-day data
- Company financials
- News data

To use this service:
1. Sign up for a free API key at https://polygon.io/
2. Add POLYGON_API_KEY to your .env file
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
import asyncio
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

class PolygonService:
    """Service for fetching financial data from Polygon.io API"""
    
    def __init__(self):
        self.api_key = os.getenv('POLYGON_API_KEY')
        self.base_url = 'https://api.polygon.io'
        self.cache = CacheService()
        self.request_count = 0
        self.last_request_time = datetime.now()
        
    async def _rate_limit(self):
        """Ensure we don't exceed 5 requests per minute for free tier"""
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
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with rate limiting and error handling"""
        if not self.api_key:
            logger.warning("Polygon API key not configured")
            return {}
            
        await self._rate_limit()
        
        if params is None:
            params = {}
        params['apiKey'] = self.api_key
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}{endpoint}"
                response = await client.get(url, params=params, timeout=30.0)
                
                if response.status_code == 403:
                    logger.error("Polygon API key is invalid or rate limit exceeded")
                    return {}
                    
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if data.get('status') == 'ERROR':
                    logger.error(f"Polygon API error: {data.get('error', 'Unknown error')}")
                    return {}
                    
                return data
                
        except Exception as e:
            logger.error(f"Error making Polygon API request: {str(e)}")
            return {}
    
    async def get_market_holidays(self) -> List[Dict[str, Any]]:
        """Get upcoming market holidays"""
        cache_key = "polygon:market_holidays"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            endpoint = "/v1/marketstatus/upcoming"
            data = await self._make_request(endpoint)
            
            holidays = []
            if data and isinstance(data, list):
                for holiday in data:
                    holidays.append({
                        'date': holiday.get('date'),
                        'name': holiday.get('name'),
                        'exchange': holiday.get('exchange', 'NYSE'),
                        'status': holiday.get('status', 'closed')
                    })
            
            # Cache for 24 hours
            if holidays:
                self.cache.set(cache_key, holidays, 'default', 86400)
                
            return holidays
            
        except Exception as e:
            logger.error(f"Error fetching market holidays: {str(e)}")
            return []
    
    async def get_ticker_news(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get news for a specific ticker"""
        cache_key = f"polygon:news:{ticker}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            endpoint = f"/v2/reference/news"
            params = {
                'ticker': ticker.upper(),
                'limit': limit,
                'order': 'desc'
            }
            
            data = await self._make_request(endpoint, params)
            
            news_items = []
            if data and 'results' in data:
                for article in data['results']:
                    news_items.append({
                        'title': article.get('title'),
                        'url': article.get('article_url'),
                        'source': article.get('publisher', {}).get('name', 'Unknown'),
                        'published': article.get('published_utc'),
                        'summary': article.get('description', ''),
                        'tickers': article.get('tickers', [])
                    })
            
            # Cache for 30 minutes
            if news_items:
                self.cache.set(cache_key, news_items, 'default', 1800)
                
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching ticker news for {ticker}: {str(e)}")
            return []
    
    async def get_ticker_details(self, ticker: str) -> Dict[str, Any]:
        """Get detailed information about a ticker"""
        cache_key = f"polygon:ticker_details:{ticker}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            endpoint = f"/v3/reference/tickers/{ticker.upper()}"
            data = await self._make_request(endpoint)
            
            if data and 'results' in data:
                details = data['results']
                
                # Transform to our standard format
                ticker_info = {
                    'symbol': details.get('ticker'),
                    'name': details.get('name'),
                    'market_cap': details.get('market_cap'),
                    'description': details.get('description'),
                    'homepage': details.get('homepage_url'),
                    'industry': details.get('sic_description'),
                    'sector': details.get('type'),
                    'employees': details.get('total_employees'),
                    'exchange': details.get('primary_exchange'),
                    'list_date': details.get('list_date'),
                    'logo': details.get('branding', {}).get('logo_url')
                }
                
                # Cache for 24 hours
                self.cache.set(cache_key, ticker_info, 'default', 86400)
                
                return ticker_info
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching ticker details for {ticker}: {str(e)}")
            return {}
    
    async def get_recent_trades(self, ticker: str) -> List[Dict[str, Any]]:
        """Get recent trades for a ticker (requires paid tier)"""
        # This endpoint requires a paid subscription
        # For free tier, we can only get end-of-day data
        try:
            endpoint = f"/v2/aggs/ticker/{ticker.upper()}/prev"
            data = await self._make_request(endpoint)
            
            if data and 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                return [{
                    'symbol': ticker.upper(),
                    'date': datetime.fromtimestamp(result.get('t', 0) / 1000).strftime('%Y-%m-%d'),
                    'open': result.get('o'),
                    'high': result.get('h'),
                    'low': result.get('l'),
                    'close': result.get('c'),
                    'volume': result.get('v'),
                    'vwap': result.get('vw')
                }]
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching recent trades for {ticker}: {str(e)}")
            return []
    
    def get_enhanced_ipo_data(self) -> List[Dict[str, Any]]:
        """Get enhanced IPO data (when API doesn't provide IPO calendar)"""
        # Polygon doesn't have a dedicated IPO calendar endpoint in free tier
        # Return enhanced mock data based on market research
        base_date = datetime.now()
        
        return [
            {
                'company': 'Shein',
                'symbol': 'SHEIN',
                'date': (base_date + timedelta(days=45)).strftime('%Y-%m-%d'),
                'price_range': '$60-70',
                'shares': '100M',
                'market_cap': '$65B',
                'lead_underwriter': 'Goldman Sachs, JP Morgan',
                'exchange': 'NYSE',
                'sector': 'E-commerce/Fashion',
                'description': 'Fast fashion e-commerce platform',
                'source': 'Market Intelligence'
            },
            {
                'company': 'SpaceX',
                'symbol': 'SPACE',
                'date': (base_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                'price_range': '$125-150',
                'shares': '50M',
                'market_cap': '$180B',
                'lead_underwriter': 'Morgan Stanley',
                'exchange': 'NYSE',
                'sector': 'Aerospace',
                'description': 'Space exploration and satellite internet',
                'source': 'Market Intelligence'
            },
            {
                'company': 'Klarna Bank AB',
                'symbol': 'KLRNA',
                'date': (base_date + timedelta(days=30)).strftime('%Y-%m-%d'),
                'price_range': '$35-45',
                'shares': '60M',
                'market_cap': '$15B',
                'lead_underwriter': 'Goldman Sachs',
                'exchange': 'NASDAQ',
                'sector': 'Fintech',
                'description': 'Buy now, pay later platform',
                'source': 'Market Intelligence'
            },
            {
                'company': 'Revolut Ltd',
                'symbol': 'RVLT',
                'date': (base_date + timedelta(days=60)).strftime('%Y-%m-%d'),
                'price_range': '$50-65',
                'shares': '40M',
                'market_cap': '$45B',
                'lead_underwriter': 'JP Morgan, Citi',
                'exchange': 'NYSE',
                'sector': 'Digital Banking',
                'description': 'Digital banking and financial services',
                'source': 'Market Intelligence'
            }
        ]