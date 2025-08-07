from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Dict, Any, Optional
import logging
from services.watchlist_service import WatchlistService
from pydantic import BaseModel
import jwt
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

# Initialize watchlist service
watchlist_service = WatchlistService()

class AddWatchlistItemRequest(BaseModel):
    symbol: str
    symbol_type: str

def get_user_id_from_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from JWT token in Authorization header."""
    if not authorization or not authorization.startswith('Bearer '):
        # For development/testing, use a mock user ID
        if os.getenv('ENVIRONMENT') == 'development' or True:  # Always use mock for now
            logger.info("Using mock user ID for development")
            return '12345678-1234-5678-9012-123456789012'
        
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace('Bearer ', '')
    
    try:
        # For development, return mock user ID
        logger.info("Using mock user ID from token")
        return '12345678-1234-5678-9012-123456789012'
        
        # In production, you would decode the actual JWT token from Supabase
        # payload = jwt.decode(token, options={"verify_signature": False})
        # user_id = payload.get('sub')
        # if not user_id:
        #     raise HTTPException(status_code=401, detail="Invalid token")
        # return user_id
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("")
async def get_user_watchlist(
    user_id: str = Depends(get_user_id_from_token)
) -> List[Dict[str, Any]]:
    """
    Get user's complete watchlist with current market data.
    
    Returns:
        List of watchlist items with enriched market data
    """
    try:
        logger.info(f"Fetching watchlist for user {user_id}")
        watchlist = await watchlist_service.get_user_watchlist(user_id)
        
        logger.info(f"Retrieved {len(watchlist)} items from watchlist for user {user_id}")
        return watchlist
        
    except Exception as e:
        logger.error(f"Error fetching watchlist for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")

@router.post("")
async def add_to_watchlist(
    request: AddWatchlistItemRequest,
    user_id: str = Depends(get_user_id_from_token)
) -> Dict[str, Any]:
    """
    Add a symbol to user's watchlist.
    
    Args:
        request: Symbol and symbol type to add
        
    Returns:
        Success status and watchlist item data
    """
    try:
        logger.info(f"Adding {request.symbol} to watchlist for user {user_id}")
        
        result = await watchlist_service.add_to_watchlist(
            user_id, 
            request.symbol, 
            request.symbol_type
        )
        
        if result['success']:
            logger.info(f"Successfully added {request.symbol} to watchlist")
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding {request.symbol} to watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add symbol to watchlist")

@router.delete("/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    user_id: str = Depends(get_user_id_from_token)
) -> Dict[str, Any]:
    """
    Remove a symbol from user's watchlist.
    
    Args:
        symbol: Symbol to remove from watchlist
        
    Returns:
        Success status message
    """
    try:
        logger.info(f"Removing {symbol} from watchlist for user {user_id}")
        
        result = await watchlist_service.remove_from_watchlist(user_id, symbol)
        
        if result['success']:
            logger.info(f"Successfully removed {symbol} from watchlist")
            return result
        else:
            raise HTTPException(status_code=404, detail=result['message'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing {symbol} from watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove symbol from watchlist")

@router.get("/count")
async def get_watchlist_count(
    user_id: str = Depends(get_user_id_from_token)
) -> Dict[str, int]:
    """
    Get the number of items in user's watchlist.
    
    Returns:
        Dictionary with count of watchlist items
    """
    try:
        logger.info(f"Getting watchlist count for user {user_id}")
        
        count = await watchlist_service.get_watchlist_count(user_id)
        
        return {"count": count}
        
    except Exception as e:
        logger.error(f"Error getting watchlist count for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get watchlist count")

@router.get("/check/{symbol}")
async def check_symbol_in_watchlist(
    symbol: str,
    user_id: str = Depends(get_user_id_from_token)
) -> Dict[str, bool]:
    """
    Check if a symbol is in user's watchlist.
    
    Args:
        symbol: Symbol to check
        
    Returns:
        Dictionary indicating if symbol is in watchlist
    """
    try:
        logger.info(f"Checking if {symbol} is in watchlist for user {user_id}")
        
        is_in_watchlist = await watchlist_service.is_symbol_in_watchlist(user_id, symbol)
        
        return {
            "symbol": symbol.upper(),
            "in_watchlist": is_in_watchlist
        }
        
    except Exception as e:
        logger.error(f"Error checking {symbol} in watchlist for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check watchlist status")

@router.get("/symbols")
async def get_watchlist_symbols_only(
    user_id: str = Depends(get_user_id_from_token)
) -> List[str]:
    """
    Get just the symbols from user's watchlist (lightweight endpoint).
    
    Returns:
        List of symbols in user's watchlist
    """
    try:
        logger.info(f"Fetching watchlist symbols for user {user_id}")
        watchlist = await watchlist_service.get_user_watchlist(user_id)
        
        symbols = [item['symbol'] for item in watchlist]
        
        logger.info(f"Retrieved {len(symbols)} symbols from watchlist")
        return symbols
        
    except Exception as e:
        logger.error(f"Error fetching watchlist symbols for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist symbols")