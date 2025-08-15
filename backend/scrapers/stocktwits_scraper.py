from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import re
from scrapers.base_scraper import BaseScraper
from services.sentiment_service import SentimentService
import logging

logger = logging.getLogger(__name__)

class StockTwitsScraper(BaseScraper):
    """
    Scraper for StockTwits social sentiment data.
    """
    
    def __init__(self):
        super().__init__("https://api.stocktwits.com/api/2", rate_limit=1.0)
        self.sentiment_service = SentimentService()
    
    def scrape_symbol_sentiment(self, symbol: str, limit: int = 30) -> Dict[str, Any]:
        """
        Scrape sentiment data for a specific symbol from StockTwits.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            limit: Number of messages to analyze
            
        Returns:
            Dict with sentiment analysis results
        """
        try:
            # StockTwits API endpoint for symbol stream
            url = f"{self.base_url}/streams/symbol/{symbol.upper()}.json?max={limit}"
            
            # Fetch data from StockTwits
            html = self.fetch_page(url)
            if not html:
                logger.error(f"Failed to fetch StockTwits data for {symbol}")
                return self._get_empty_sentiment_data(symbol)
            
            try:
                data = json.loads(html)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from StockTwits for {symbol}")
                return self._get_empty_sentiment_data(symbol)
            
            if 'messages' not in data:
                logger.error(f"No messages found in StockTwits response for {symbol}")
                return self._get_empty_sentiment_data(symbol)
            
            messages = data['messages']
            analyzed_messages = []
            
            # Analyze each message
            for message in messages:
                try:
                    text = message.get('body', '')
                    created_at = message.get('created_at', '')
                    user = message.get('user', {})
                    
                    # Get sentiment from StockTwits (if available)
                    stocktwits_sentiment = message.get('entities', {}).get('sentiment')
                    
                    # Analyze sentiment using our service
                    our_sentiment = self.sentiment_service.analyze_text(text)
                    
                    message_data = {
                        'id': message.get('id'),
                        'text': text,
                        'created_at': created_at,
                        'user': {
                            'username': user.get('username', ''),
                            'followers': user.get('followers', 0)
                        },
                        'stocktwits_sentiment': stocktwits_sentiment,
                        'our_sentiment': our_sentiment,
                        'likes': message.get('likes', {}).get('total', 0)
                    }
                    
                    analyzed_messages.append(message_data)
                    
                except Exception as e:
                    logger.error(f"Error processing StockTwits message: {str(e)}")
                    continue
            
            # Calculate overall sentiment
            sentiments = [msg['our_sentiment'] for msg in analyzed_messages]
            overall_sentiment = self.sentiment_service.get_overall_sentiment(sentiments)
            
            # Add StockTwits-specific metrics
            bullish_st = sum(1 for msg in analyzed_messages 
                           if msg.get('stocktwits_sentiment', {}).get('basic') == 'Bullish')
            bearish_st = sum(1 for msg in analyzed_messages 
                           if msg.get('stocktwits_sentiment', {}).get('basic') == 'Bearish')
            
            result = {
                'symbol': symbol.upper(),
                'source': 'stocktwits',
                'messages_analyzed': len(analyzed_messages),
                'overall_sentiment': overall_sentiment,
                'stocktwits_sentiment': {
                    'bullish_count': bullish_st,
                    'bearish_count': bearish_st,
                    'bullish_ratio': bullish_st / len(analyzed_messages) if analyzed_messages else 0,
                    'bearish_ratio': bearish_st / len(analyzed_messages) if analyzed_messages else 0
                },
                'recent_messages': analyzed_messages[:10],  # Top 10 for display
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error scraping StockTwits for {symbol}: {str(e)}")
            return self._get_empty_sentiment_data(symbol)
    
    def scrape_trending_symbols(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape trending symbols from StockTwits.
        
        Args:
            limit: Number of trending symbols to return
            
        Returns:
            List of trending symbols with basic sentiment
        """
        try:
            # StockTwits trending endpoint
            url = f"{self.base_url}/trending/symbols.json?limit={limit}"
            
            html = self.fetch_page(url)
            if not html:
                logger.error("Failed to fetch StockTwits trending data")
                return []
            
            try:
                data = json.loads(html)
            except json.JSONDecodeError:
                logger.error("Invalid JSON response from StockTwits trending")
                return []
            
            if 'symbols' not in data:
                logger.error("No symbols found in StockTwits trending response")
                return []
            
            trending_symbols = []
            
            for symbol_data in data['symbols']:
                symbol = symbol_data.get('symbol', '')
                title = symbol_data.get('title', '')
                
                trending_symbols.append({
                    'symbol': symbol,
                    'title': title,
                    'exchange': symbol_data.get('exchange', ''),
                    'is_following': symbol_data.get('is_following', False),
                    'watchlist_count': symbol_data.get('watchlist_count', 0)
                })
            
            return trending_symbols
            
        except Exception as e:
            logger.error(f"Error scraping StockTwits trending: {str(e)}")
            return []
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Main scrape method - get trending symbols"""
        return self.scrape_trending_symbols()
    
    def _get_empty_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """Return empty sentiment data when scraping fails"""
        return {
            'symbol': symbol.upper(),
            'source': 'stocktwits',
            'messages_analyzed': 0,
            'overall_sentiment': {
                'average_sentiment': 0,
                'bullish_ratio': 0,
                'bearish_ratio': 0,
                'neutral_ratio': 0,
                'total_count': 0
            },
            'stocktwits_sentiment': {
                'bullish_count': 0,
                'bearish_count': 0,
                'bullish_ratio': 0,
                'bearish_ratio': 0
            },
            'recent_messages': [],
            'timestamp': datetime.now().isoformat(),
            'error': 'Failed to fetch StockTwits data'
        }
    
