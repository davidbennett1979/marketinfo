import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

class FinancialModelingPrepService:
    """
    Service for fetching financial data from Financial Modeling Prep API.
    Free tier: 250 API calls per day
    """
    
    def __init__(self):
        self.api_key = os.getenv('FINANCIAL_MODELING_PREP_API_KEY', 'demo')
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.cache = CacheService()
        
        if self.api_key == 'demo':
            logger.warning("Using demo API key for Financial Modeling Prep. Some features may be limited.")
    
    async def get_earnings_calendar(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming earnings calendar from Financial Modeling Prep.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming earnings with real data
        """
        cache_key = f"fmp:earnings_calendar:{days_ahead}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Calculate date range
            from_date = datetime.now().strftime('%Y-%m-%d')
            to_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/earning_calendar"
            params = {
                'from': from_date,
                'to': to_date,
                'apikey': self.api_key
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                earnings_data = response.json()
                
                # Process and format the data
                formatted_earnings = []
                for earning in earnings_data[:50]:  # Limit to 50 results
                    formatted_earnings.append({
                        'symbol': earning.get('symbol', ''),
                        'company_name': earning.get('name', ''),
                        'earnings_date': earning.get('date', ''),
                        'earnings_time': earning.get('time', 'TBD'),
                        'eps_estimate': earning.get('epsEstimated'),
                        'eps_actual': earning.get('eps'),
                        'revenue_estimate': earning.get('revenueEstimated'),
                        'revenue_actual': earning.get('revenue'),
                        'fiscal_period': earning.get('fiscalDateEnding', ''),
                        'confirmed': True  # FMP data is confirmed
                    })
                
                # Sort by date
                formatted_earnings.sort(key=lambda x: x['earnings_date'])
                
                # Cache for 4 hours
                self.cache.set(cache_key, formatted_earnings, 'earnings', ttl=14400)
                
                logger.info(f"Retrieved {len(formatted_earnings)} earnings from Financial Modeling Prep")
                return formatted_earnings
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.error("FMP API key is invalid or rate limit exceeded")
            else:
                logger.error(f"HTTP error fetching earnings calendar: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching FMP earnings calendar: {str(e)}")
            return []
    
    async def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed company profile information.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Company profile data
        """
        cache_key = f"fmp:company_profile:{symbol}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.base_url}/profile/{symbol}"
            params = {'apikey': self.api_key}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                if data:
                    profile = data[0] if isinstance(data, list) else data
                    
                    # Cache for 24 hours
                    self.cache.set(cache_key, profile, 'company', ttl=86400)
                    return profile
                    
        except Exception as e:
            logger.error(f"Error fetching company profile for {symbol}: {str(e)}")
            
        return None
    
    async def get_stock_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get latest news for a specific stock.
        
        Args:
            symbol: Stock symbol
            limit: Number of news items to retrieve
            
        Returns:
            List of news articles
        """
        cache_key = f"fmp:stock_news:{symbol}:{limit}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.base_url}/stock_news"
            params = {
                'tickers': symbol,
                'limit': limit,
                'apikey': self.api_key
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                news_data = response.json()
                
                # Format the news data
                formatted_news = []
                for article in news_data:
                    formatted_news.append({
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'source': article.get('site', ''),
                        'published_at': article.get('publishedDate', ''),
                        'symbol': symbol,
                        'image': article.get('image', ''),
                        'text': article.get('text', '')[:200] + '...'  # Truncate text
                    })
                
                # Cache for 30 minutes
                self.cache.set(cache_key, formatted_news, 'news', ttl=1800)
                
                return formatted_news
                
        except Exception as e:
            logger.error(f"Error fetching stock news for {symbol}: {str(e)}")
            return []