import redis
import json
from typing import Optional, Any, Callable, Dict
from datetime import timedelta
import logging
import os
import asyncio

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
            'technical': 900,       # 15 minutes
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
        """Clear all keys matching a pattern.
        For small keyspaces (<=1000 keys), use KEYS for speed; otherwise SCAN to avoid blocking.
        """
        try:
            total = 0
            try:
                dbsize = int(self.redis_client.dbsize())
            except Exception:
                dbsize = None

            if dbsize is not None and dbsize <= 1000:
                keys = self.redis_client.keys(pattern)
                if keys:
                    try:
                        total += int(self.redis_client.delete(*keys))
                    except Exception as e:
                        logger.warning(f"Bulk delete failed for {len(keys)} keys: {e}")
                return total

            for key in self.redis_client.scan_iter(pattern):
                try:
                    total += int(self.redis_client.delete(key))
                except Exception as inner_e:
                    logger.warning(f"Failed to delete key {key}: {inner_e}")
            return total
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
    
    async def get_or_fetch(
        self, 
        key: str, 
        fetch_func: Callable[[], Any],
        cache_type: str = 'default',
        custom_ttl: Optional[int] = None
    ) -> Optional[Any]:
        """
        Get value from cache or fetch it if not present.
        Uses request coalescing to prevent duplicate API calls.
        
        Args:
            key: Cache key
            fetch_func: Async function to fetch data if not in cache
            cache_type: Type of cache for TTL
            custom_ttl: Custom TTL in seconds
            
        Returns:
            Cached or fetched value
        """
        # Import here to avoid circular dependency
        from services.request_coalescer import request_coalescer
        
        # Try to get from cache first
        cached_value = self.get(key)
        if cached_value is not None:
            logger.info(f"Cache hit for key: {key}")
            return cached_value
        
        logger.info(f"Cache miss for key: {key}, fetching...")
        
        # Create a coalescing key
        coalesce_key = f"coalesce:{key}"
        
        # Define cache function
        async def cache_result(value):
            if value is not None:
                self.set(key, value, cache_type, custom_ttl)
        
        # Use request coalescer to fetch data
        try:
            result = await request_coalescer.coalesce(
                coalesce_key, 
                fetch_func,
                cache_result
            )
            return result
        except Exception as e:
            logger.error(f"Error fetching data for key {key}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = self.redis_client.info('stats')
            return {
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                ),
                'total_keys': self.redis_client.dbsize(),
                'memory_used': info.get('used_memory_human', 'N/A')
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
