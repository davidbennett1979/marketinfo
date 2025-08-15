from fastapi import APIRouter, HTTPException
from typing import List, Optional
from scrapers.news_scraper import NewsScraperRSS, EarningsCalendarScraper
from services.cache_service import CacheService
import logging

router = APIRouter(prefix="/api/news", tags=["news"])
cache = CacheService()
logger = logging.getLogger(__name__)

@router.get("/latest")
async def get_latest_news(limit: int = 50):
    """Get latest financial news from multiple sources"""
    cache_key = f"news:latest:{limit}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Fetch fresh data
    try:
        scraper = NewsScraperRSS()
        articles = scraper.scrape_all_feeds()
        
        # Limit results
        articles = articles[:limit]
        
        # Cache the results
        cache.set(cache_key, articles, 'news')
        
        return articles
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")

@router.get("/earnings-calendar")
async def get_earnings_calendar():
    """Get today's and this week's earnings calendar"""
    cache_key = "earnings:calendar:today"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Use the real earnings calendar scraper
    try:
        scraper = EarningsCalendarScraper()
        earnings_data = scraper.scrape()
        
        # Cache the results if we got data
        if earnings_data:
            cache.set(cache_key, earnings_data, 'company_info')
            return earnings_data
        else:
            # No earnings data available
            return []
            
    except Exception as e:
        logger.error(f"Error fetching earnings calendar: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch earnings calendar")

@router.get("/short-interest")
async def get_short_interest():
    """Get high short interest stocks"""
    cache_key = "short:interest:high"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Use the real short interest scraper
    try:
        from scrapers.news_scraper import ShortInterestScraper
        scraper = ShortInterestScraper()
        short_data = scraper.scrape()
        
        # Cache the results if we got data
        if short_data:
            cache.set(cache_key, short_data, 'company_info')
            return short_data
        else:
            # No short interest data available
            return []
            
    except Exception as e:
        logger.error(f"Error fetching short interest data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch short interest data")