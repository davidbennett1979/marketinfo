import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import praw
from services.sentiment_service import SentimentService
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

class RedditService:
    """
    Service for fetching and analyzing Reddit posts from financial subreddits.
    """
    
    def __init__(self):
        self.reddit = None
        self.sentiment_service = SentimentService()
        self.cache = CacheService()
        
        # Financial subreddits to monitor
        self.subreddits = [
            'wallstreetbets',
            'stocks', 
            'investing',
            'SecurityAnalysis',
            'ValueInvesting',
            'StockMarket',
            'pennystocks',
            'cryptocurrency'
        ]
        
        self._initialize_reddit()
    
    def _initialize_reddit(self):
        """
        Initialize Reddit API connection using PRAW.
        
        Note: Requires Reddit app credentials in environment variables:
        - REDDIT_CLIENT_ID: Your Reddit app client ID
        - REDDIT_CLIENT_SECRET: Your Reddit app client secret
        
        If credentials are not provided, the service will return mock data.
        """
        try:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'TradingDashboard/1.0')
            
            if not client_id or not client_secret:
                logger.warning("Reddit API credentials not found. Reddit features will be disabled.")
                return
            
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            
            # Test the connection
            self.reddit.user.me()
            logger.info("Reddit API connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {str(e)}")
            self.reddit = None
    
    async def get_subreddit_sentiment(self, subreddit_name: str, symbol: str = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get sentiment analysis for a specific subreddit.
        
        Args:
            subreddit_name: Name of the subreddit (e.g., 'wallstreetbets')
            symbol: Optional stock symbol to filter posts
            limit: Number of posts to analyze
            
        Returns:
            Dict with sentiment analysis results
        """
        if not self.reddit:
            return self._get_mock_sentiment_data(subreddit_name, symbol)
        
        cache_key = f"reddit:{subreddit_name}:{symbol or 'all'}:{limit}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            # Get hot posts
            for submission in subreddit.hot(limit=limit):
                # Skip pinned posts
                if submission.stickied:
                    continue
                
                # Filter by symbol if provided
                if symbol and symbol.upper() not in submission.title.upper():
                    continue
                
                post_data = {
                    'id': submission.id,
                    'title': submission.title,
                    'selftext': submission.selftext,
                    'score': submission.score,
                    'upvote_ratio': submission.upvote_ratio,
                    'num_comments': submission.num_comments,
                    'created_utc': submission.created_utc,
                    'url': f"https://reddit.com{submission.permalink}"
                }
                
                posts.append(post_data)
            
            # Analyze sentiment for each post
            sentiments = []
            for post in posts:
                text = f"{post['title']} {post['selftext']}"
                sentiment = self.sentiment_service.analyze_text(text)
                sentiment['post_id'] = post['id']
                sentiment['score'] = post['score']
                sentiment['upvote_ratio'] = post['upvote_ratio']
                sentiments.append(sentiment)
            
            # Calculate overall sentiment
            overall_sentiment = self.sentiment_service.get_overall_sentiment(sentiments)
            
            result = {
                'subreddit': subreddit_name,
                'symbol': symbol,
                'overall_sentiment': overall_sentiment,
                'posts_analyzed': len(posts),
                'top_posts': posts[:5],  # Include top 5 posts for reference
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the result for 30 minutes
            self.cache.set(cache_key, result, 'sentiment')
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {str(e)}")
            return self._get_mock_sentiment_data(subreddit_name, symbol)
    
    async def get_wallstreetbets_trending(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending stocks/topics from r/wallstreetbets"""
        cache_key = f"reddit:wsb:trending:{limit}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            if not self.reddit:
                return self._get_mock_trending_data()
            
            subreddit = self.reddit.subreddit('wallstreetbets')
            trending_posts = []
            
            for submission in subreddit.hot(limit=limit):
                if submission.stickied:
                    continue
                
                # Extract potential stock symbols from title
                import re
                symbols = re.findall(r'\b[A-Z]{2,5}\b', submission.title)
                
                sentiment = self.sentiment_service.analyze_text(
                    f"{submission.title} {submission.selftext}"
                )
                
                post_data = {
                    'title': submission.title,
                    'score': submission.score,
                    'num_comments': submission.num_comments,
                    'symbols': symbols,
                    'sentiment': sentiment,
                    'url': f"https://reddit.com{submission.permalink}",
                    'created_utc': submission.created_utc
                }
                
                trending_posts.append(post_data)
            
            # Sort by score (popularity)
            trending_posts.sort(key=lambda x: x['score'], reverse=True)
            
            # Cache for 15 minutes
            self.cache.set(cache_key, trending_posts, 'sentiment')
            
            return trending_posts
            
        except Exception as e:
            logger.error(f"Error fetching WSB trending: {str(e)}")
            return self._get_mock_trending_data()
    
    def _get_mock_sentiment_data(self, subreddit_name: str, symbol: str = None) -> Dict[str, Any]:
        """Return mock sentiment data when Reddit API is unavailable"""
        return {
            'subreddit': subreddit_name,
            'symbol': symbol,
            'overall_sentiment': {
                'average_sentiment': 0.15,
                'bullish_ratio': 0.45,
                'bearish_ratio': 0.25,
                'neutral_ratio': 0.30,
                'total_count': 50
            },
            'posts_analyzed': 50,
            'top_posts': [
                {
                    'title': f'Sample bullish post about {symbol or "the market"}',
                    'score': 1250,
                    'num_comments': 234
                }
            ],
            'timestamp': datetime.now().isoformat(),
            'mock_data': True
        }
    
    def _get_mock_trending_data(self) -> List[Dict[str, Any]]:
        """Return mock trending data when Reddit API is unavailable"""
        return [
            {
                'title': 'TSLA to the moon! 🚀',
                'score': 2500,
                'num_comments': 450,
                'symbols': ['TSLA'],
                'sentiment': {'sentiment_score': 0.6, 'classification': 'bullish'},
                'mock_data': True
            },
            {
                'title': 'AAPL earnings play discussion',
                'score': 1800,
                'num_comments': 320,
                'symbols': ['AAPL'],
                'sentiment': {'sentiment_score': 0.2, 'classification': 'neutral'},
                'mock_data': True
            }
        ]