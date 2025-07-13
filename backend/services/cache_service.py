import redis
import json
from typing import Optional, Any
from datetime import timedelta
import logging
import os

logger = logging.getLogger(__name__)

class CacheService:
    """Redis caching service for storing API responses"""
    
    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Default cache times (in seconds)
        self.CACHE_TIMES = {
            'stock_price': 300,      # 5 minutes
            'crypto_price': 180,     # 3 minutes
            'market_indices': 300,   # 5 minutes
            'news': 900,            # 15 minutes
            'historical': 3600,     # 1 hour
            'company_info': 86400,  # 24 hours
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, cache_type: str = 'default', 
            custom_ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = custom_ttl or self.CACHE_TIMES.get(cache_type, 300)
            serialized_value = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing pattern from cache: {str(e)}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache existence: {str(e)}")
            return False
    
    # Helper methods for specific data types
    def get_stock_price(self, symbol: str) -> Optional[dict]:
        """Get cached stock price"""
        return self.get(f"stock:price:{symbol}")
    
    def set_stock_price(self, symbol: str, data: dict) -> bool:
        """Cache stock price"""
        return self.set(f"stock:price:{symbol}", data, 'stock_price')
    
    def get_crypto_price(self, coin_id: str) -> Optional[dict]:
        """Get cached crypto price"""
        return self.get(f"crypto:price:{coin_id}")
    
    def set_crypto_price(self, coin_id: str, data: dict) -> bool:
        """Cache crypto price"""
        return self.set(f"crypto:price:{coin_id}", data, 'crypto_price')
    
    def get_market_indices(self) -> Optional[list]:
        """Get cached market indices"""
        return self.get("market:indices")
    
    def set_market_indices(self, data: list) -> bool:
        """Cache market indices"""
        return self.set("market:indices", data, 'market_indices')
    
    def get_news(self, category: str = 'general') -> Optional[list]:
        """Get cached news"""
        return self.get(f"news:{category}")
    
    def set_news(self, category: str, data: list) -> bool:
        """Cache news articles"""
        return self.set(f"news:{category}", data, 'news')