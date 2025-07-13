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
    
    # For MVP, return mock data (real scraping can be complex)
    # In production, you'd use the EarningsCalendarScraper
    mock_earnings = [
        {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "earnings_date": "2024-01-25",
            "earnings_time": "after_close",
            "estimated_eps": 1.95
        },
        {
            "symbol": "MSFT",
            "company_name": "Microsoft Corporation",
            "earnings_date": "2024-01-24",
            "earnings_time": "after_close",
            "estimated_eps": 2.65
        },
        {
            "symbol": "GOOGL",
            "company_name": "Alphabet Inc.",
            "earnings_date": "2024-01-30",
            "earnings_time": "after_close",
            "estimated_eps": 1.45
        }
    ]
    
    # Cache the results
    cache.set(cache_key, mock_earnings, 'company_info')
    
    return mock_earnings

@router.get("/short-interest")
async def get_short_interest():
    """Get high short interest stocks"""
    cache_key = "short:interest:high"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # For MVP, return mock data
    mock_short_data = [
        {
            "symbol": "GME",
            "company_name": "GameStop Corp.",
            "short_interest_percent": "23.5%",
            "days_to_cover": 2.1
        },
        {
            "symbol": "AMC",
            "company_name": "AMC Entertainment",
            "short_interest_percent": "19.8%",
            "days_to_cover": 1.8
        },
        {
            "symbol": "BBBY",
            "company_name": "Bed Bath & Beyond",
            "short_interest_percent": "45.2%",
            "days_to_cover": 3.5
        }
    ]
    
    # Cache the results
    cache.set(cache_key, mock_short_data, 'company_info')
    
    return mock_short_data