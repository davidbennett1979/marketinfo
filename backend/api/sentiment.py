from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from services.reddit_service import RedditService
from services.sentiment_service import SentimentService
from scrapers.stocktwits_scraper import StockTwitsScraper
from services.cache_service import CacheService
import logging

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])
cache = CacheService()
logger = logging.getLogger(__name__)

@router.get("/reddit/{subreddit}")
async def get_reddit_sentiment(
    subreddit: str,
    symbol: Optional[str] = None,
    limit: int = Query(default=50, le=100)
):
    """Get sentiment analysis from a specific subreddit"""
    try:
        reddit_service = RedditService()
        result = await reddit_service.get_subreddit_sentiment(subreddit, symbol, limit)
        return result
    except Exception as e:
        logger.error(f"Error getting Reddit sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch Reddit sentiment")

@router.get("/reddit/wsb/trending")
async def get_wallstreetbets_trending(limit: int = Query(default=20, le=50)):
    """Get trending posts from r/wallstreetbets"""
    try:
        reddit_service = RedditService()
        trending = await reddit_service.get_wallstreetbets_trending(limit)
        return trending
    except Exception as e:
        logger.error(f"Error getting WSB trending: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch WSB trending")

@router.get("/stocktwits/{symbol}")
async def get_stocktwits_sentiment(symbol: str, limit: int = Query(default=30, le=100)):
    """Get sentiment analysis from StockTwits for a specific symbol"""
    cache_key = f"sentiment:stocktwits:{symbol}:{limit}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        scraper = StockTwitsScraper()
        result = scraper.scrape_symbol_sentiment(symbol, limit)
        scraper.close()
        
        # Cache for 30 minutes
        cache.set(cache_key, result, 'sentiment')
        
        return result
    except Exception as e:
        logger.error(f"Error getting StockTwits sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch StockTwits sentiment")

@router.get("/stocktwits/trending")
async def get_stocktwits_trending(limit: int = Query(default=20, le=50)):
    """Get trending symbols from StockTwits"""
    cache_key = f"sentiment:stocktwits:trending:{limit}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        scraper = StockTwitsScraper()
        result = scraper.scrape_trending_symbols(limit)
        scraper.close()
        
        # Cache for 15 minutes
        cache.set(cache_key, result, 'sentiment')
        
        return result
    except Exception as e:
        logger.error(f"Error getting StockTwits trending: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch StockTwits trending")

@router.get("/combined/{symbol}")
async def get_combined_sentiment(symbol: str):
    """Get combined sentiment analysis from multiple sources"""
    cache_key = f"sentiment:combined:{symbol}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        results = {}
        
        # Get Reddit sentiment from multiple subreddits
        reddit_service = RedditService()
        wsb_sentiment = await reddit_service.get_subreddit_sentiment('wallstreetbets', symbol, 30)
        stocks_sentiment = await reddit_service.get_subreddit_sentiment('stocks', symbol, 20)
        
        # Get StockTwits sentiment
        scraper = StockTwitsScraper()
        stocktwits_sentiment = scraper.scrape_symbol_sentiment(symbol, 30)
        scraper.close()
        
        results = {
            'symbol': symbol.upper(),
            'sources': {
                'reddit_wsb': wsb_sentiment,
                'reddit_stocks': stocks_sentiment,
                'stocktwits': stocktwits_sentiment
            }
        }
        
        # Calculate overall combined sentiment
        all_sentiments = []
        
        # Add Reddit sentiments
        if wsb_sentiment.get('overall_sentiment'):
            all_sentiments.append(wsb_sentiment['overall_sentiment']['average_sentiment'])
        
        if stocks_sentiment.get('overall_sentiment'):
            all_sentiments.append(stocks_sentiment['overall_sentiment']['average_sentiment'])
        
        # Add StockTwits sentiment
        if stocktwits_sentiment.get('overall_sentiment'):
            all_sentiments.append(stocktwits_sentiment['overall_sentiment']['average_sentiment'])
        
        if all_sentiments:
            combined_score = sum(all_sentiments) / len(all_sentiments)
            
            if combined_score > 0.1:
                classification = 'bullish'
            elif combined_score < -0.1:
                classification = 'bearish'
            else:
                classification = 'neutral'
            
            results['combined_sentiment'] = {
                'score': round(combined_score, 3),
                'classification': classification,
                'confidence': round(abs(combined_score), 3),
                'sources_count': len(all_sentiments)
            }
        
        # Cache for 30 minutes
        cache.set(cache_key, results, 'sentiment')
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting combined sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch combined sentiment")

@router.post("/analyze-text")
async def analyze_text_sentiment(text: str):
    """Analyze sentiment of provided text"""
    try:
        sentiment_service = SentimentService()
        result = sentiment_service.analyze_text(text)
        return result
    except Exception as e:
        logger.error(f"Error analyzing text sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze text sentiment")