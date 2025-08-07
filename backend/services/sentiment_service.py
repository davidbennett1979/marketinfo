import re
import logging
from typing import Dict, List, Optional
from textblob import TextBlob
import asyncio

logger = logging.getLogger(__name__)

class SentimentService:
    """
    Service for analyzing sentiment of financial text.
    
    Uses TextBlob for basic sentiment analysis combined with financial keyword detection.
    Sentiment scores range from -1 (bearish) to +1 (bullish).
    
    Example:
        service = SentimentService()
        result = service.analyze_text("AAPL is going to the moon! Buy calls!")
        # Returns: {'sentiment_score': 0.65, 'classification': 'bullish', ...}
    """
    
    # Financial keywords that indicate bullish sentiment
    BULLISH_KEYWORDS = [
        'buy', 'bull', 'bullish', 'long', 'calls', 'moon', 'rocket', 'pump',
        'green', 'gains', 'profit', 'strong', 'support', 'breakout', 'rally',
        'surge', 'spike', 'climb', 'soar', 'rise', 'up', 'bullish', 'positive'
    ]
    
    # Financial keywords that indicate bearish sentiment
    BEARISH_KEYWORDS = [
        'sell', 'bear', 'bearish', 'short', 'puts', 'crash', 'dump', 'red',
        'loss', 'weak', 'resistance', 'breakdown', 'decline', 'plunge', 'drop',
        'fall', 'down', 'bearish', 'negative', 'correction', 'bubble'
    ]
    
    @staticmethod
    def analyze_text(text: str) -> Dict[str, float]:
        """
        Analyze sentiment of a given text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dict with sentiment scores and confidence
        """
        try:
            # Clean the text
            cleaned_text = SentimentService._clean_text(text)
            
            # Use TextBlob for basic sentiment analysis
            blob = TextBlob(cleaned_text)
            
            # Get polarity (-1 to 1) and subjectivity (0 to 1)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Enhance with financial keyword analysis
            keyword_sentiment = SentimentService._analyze_financial_keywords(cleaned_text)
            
            # Combine TextBlob and keyword analysis
            combined_sentiment = (polarity * 0.7) + (keyword_sentiment * 0.3)
            
            # Classify sentiment
            if combined_sentiment > 0.1:
                classification = 'bullish'
            elif combined_sentiment < -0.1:
                classification = 'bearish'
            else:
                classification = 'neutral'
            
            return {
                'sentiment_score': round(combined_sentiment, 3),
                'polarity': round(polarity, 3),
                'subjectivity': round(subjectivity, 3),
                'classification': classification,
                'confidence': round(abs(combined_sentiment), 3)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                'sentiment_score': 0.0,
                'polarity': 0.0,
                'subjectivity': 0.0,
                'classification': 'neutral',
                'confidence': 0.0
            }
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and preprocess text for sentiment analysis"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove special characters but keep spaces and periods
        text = re.sub(r'[^a-zA-Z0-9\s\.]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def _analyze_financial_keywords(text: str) -> float:
        """
        Analyze text for financial keywords and return sentiment score.
        
        Returns:
            Float between -1 and 1 indicating sentiment
        """
        words = text.lower().split()
        
        bullish_count = sum(1 for word in words if word in SentimentService.BULLISH_KEYWORDS)
        bearish_count = sum(1 for word in words if word in SentimentService.BEARISH_KEYWORDS)
        
        total_keywords = bullish_count + bearish_count
        
        if total_keywords == 0:
            return 0.0
        
        # Calculate sentiment based on keyword ratio
        sentiment = (bullish_count - bearish_count) / len(words)
        
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, sentiment * 10))
    
    @staticmethod
    def analyze_batch(texts: List[str]) -> List[Dict[str, float]]:
        """Analyze sentiment for multiple texts"""
        results = []
        for text in texts:
            result = SentimentService.analyze_text(text)
            results.append(result)
        return results
    
    @staticmethod
    def get_overall_sentiment(sentiments: List[Dict[str, float]]) -> Dict[str, any]:
        """
        Calculate overall sentiment from a list of individual sentiments.
        
        Args:
            sentiments: List of sentiment analysis results
            
        Returns:
            Dict with aggregated sentiment data
        """
        if not sentiments:
            return {
                'average_sentiment': 0.0,
                'bullish_ratio': 0.0,
                'bearish_ratio': 0.0,
                'neutral_ratio': 0.0,
                'total_count': 0
            }
        
        total_sentiment = sum(s['sentiment_score'] for s in sentiments)
        average_sentiment = total_sentiment / len(sentiments)
        
        bullish_count = sum(1 for s in sentiments if s['classification'] == 'bullish')
        bearish_count = sum(1 for s in sentiments if s['classification'] == 'bearish')
        neutral_count = sum(1 for s in sentiments if s['classification'] == 'neutral')
        
        total_count = len(sentiments)
        
        return {
            'average_sentiment': round(average_sentiment, 3),
            'bullish_ratio': round(bullish_count / total_count, 3),
            'bearish_ratio': round(bearish_count / total_count, 3),
            'neutral_ratio': round(neutral_count / total_count, 3),
            'total_count': total_count,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count
        }