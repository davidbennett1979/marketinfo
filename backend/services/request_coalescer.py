import asyncio
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timedelta
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class RequestCoalescer:
    """
    Coalesces duplicate requests to prevent multiple API calls for the same data.
    When multiple requests for the same data come in within a short time window,
    only one actual API call is made and all requesters get the same result.
    """
    
    def __init__(self, window_seconds: int = 5):
        """
        Initialize the request coalescer.
        
        Args:
            window_seconds: Time window in seconds to coalesce requests
        """
        self.window_seconds = window_seconds
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_timestamps: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def coalesce(
        self, 
        key: str, 
        fetch_func: Callable[[], Any],
        cache_func: Optional[Callable[[Any], Any]] = None
    ) -> Any:
        """
        Coalesce requests for the same key.
        
        Args:
            key: Unique identifier for the request
            fetch_func: Async function to fetch the data
            cache_func: Optional function to cache the result
            
        Returns:
            The fetched data
        """
        async with self._lock:
            # Clean up old requests
            self._cleanup_expired_requests()
            
            # Check if there's already a pending request for this key
            if key in self.pending_requests:
                future = self.pending_requests[key]
                logger.info(f"Coalescing request for key: {key}")
                # Wait for the existing request to complete
                try:
                    return await future
                except Exception as e:
                    logger.error(f"Coalesced request failed for key {key}: {e}")
                    raise
            
            # No pending request, create a new one
            future = asyncio.create_task(self._fetch_and_cleanup(key, fetch_func, cache_func))
            self.pending_requests[key] = future
            self.request_timestamps[key] = datetime.now()
            
            try:
                result = await future
                return result
            except Exception as e:
                logger.error(f"Request failed for key {key}: {e}")
                raise
    
    async def _fetch_and_cleanup(
        self, 
        key: str, 
        fetch_func: Callable[[], Any],
        cache_func: Optional[Callable[[Any], Any]] = None
    ) -> Any:
        """
        Fetch data and clean up the request from pending.
        
        Args:
            key: Request key
            fetch_func: Function to fetch data
            cache_func: Optional function to cache result
            
        Returns:
            Fetched data
        """
        try:
            # Fetch the data
            result = await fetch_func()
            
            # Cache if cache function provided
            if cache_func and result:
                try:
                    await cache_func(result)
                except Exception as e:
                    logger.error(f"Failed to cache result for key {key}: {e}")
            
            return result
        finally:
            # Always clean up the pending request
            async with self._lock:
                if key in self.pending_requests:
                    del self.pending_requests[key]
                if key in self.request_timestamps:
                    del self.request_timestamps[key]
    
    def _cleanup_expired_requests(self):
        """Remove expired requests from tracking."""
        now = datetime.now()
        expired_keys = []
        
        for key, timestamp in self.request_timestamps.items():
            if (now - timestamp).total_seconds() > self.window_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self.pending_requests:
                del self.pending_requests[key]
            if key in self.request_timestamps:
                del self.request_timestamps[key]
    
    @staticmethod
    def create_key(*args, **kwargs) -> str:
        """
        Create a unique key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Unique hash key
        """
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()


# Global instance for use across the application
request_coalescer = RequestCoalescer(window_seconds=5)