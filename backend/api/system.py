from fastapi import APIRouter, Depends
from services.cache_service import CacheService
from api.watchlist import get_user_id_from_token
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/system/cache/stats")
async def get_cache_stats(current_user: str = Depends(get_user_id_from_token)):
    """
    Get cache statistics including hit rate and memory usage.
    
    Returns:
        Cache statistics including hits, misses, hit rate, total keys, and memory usage
    """
    try:
        cache_service = CacheService()
        stats = cache_service.get_stats()
        
        return {
            "status": "success",
            "data": stats,
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "status": "error",
            "data": {},
            "message": "Failed to retrieve cache statistics"
        }

@router.get("/api/system/health")
async def health_check():
    """
    System health check endpoint.
    
    Returns:
        Health status of various system components
    """
    try:
        cache_service = CacheService()
        
        # Check Redis
        redis_healthy = False
        try:
            cache_service.redis_client.ping()
            redis_healthy = True
        except:
            pass
        
        return {
            "status": "healthy" if redis_healthy else "degraded",
            "components": {
                "redis": redis_healthy,
                "api": True
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "components": {
                "redis": False,
                "api": True
            }
        }