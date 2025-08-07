from fastapi import APIRouter, HTTPException
from typing import List, Optional
from services.stock_service import StockService
from services.cache_service import CacheService

router = APIRouter(prefix="/api/stocks", tags=["stocks"])
cache = CacheService()

@router.get("/price/{symbol}")
async def get_stock_price(symbol: str):
    """Get current stock price"""
    # Check cache first
    cached_data = cache.get_stock_price(symbol)
    if cached_data:
        return cached_data
    
    # Fetch fresh data
    data = StockService.get_stock_price(symbol)
    if not data:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Cache the result
    cache.set_stock_price(symbol, data)
    return data

@router.get("/multiple")
async def get_multiple_stocks(symbols: str):
    """Get prices for multiple stocks (comma-separated symbols)"""
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    results = StockService.get_multiple_stocks(symbol_list)
    return results

@router.get("/prices")
async def get_stock_prices(symbols: str = ""):
    """Get current prices for multiple stocks (comma-separated symbols)"""
    if not symbols:
        # Default symbols if none provided
        symbols = "AAPL,MSFT,GOOGL,TSLA,AMZN,NVDA,META,NFLX"
    
    symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
    
    if not symbol_list:
        return {}
    
    try:
        results = StockService.get_multiple_stocks(symbol_list)
        return results
    except Exception as e:
        # Return empty dict to prevent frontend crashes
        return {}

@router.get("/indices")
async def get_market_indices():
    """Get major market indices"""
    # Check cache first
    cached_data = cache.get_market_indices()
    if cached_data:
        return cached_data
    
    # Fetch fresh data
    data = StockService.get_market_indices()
    
    # Cache the result
    cache.set_market_indices(data)
    return data

@router.get("/history/{symbol}")
async def get_stock_history(symbol: str, period: str = "1mo"):
    """Get historical stock data"""
    cache_key = f"stock:history:{symbol}:{period}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Fetch fresh data
    data = StockService.get_historical_data(symbol, period)
    if not data:
        raise HTTPException(status_code=404, detail=f"Historical data for {symbol} not found")
    
    # Cache the result
    cache.set(cache_key, data, 'historical')
    return data

@router.get("/search")
async def search_stocks(q: str):
    """Search for stocks by symbol or name"""
    if len(q) < 1:
        return []
    
    results = StockService.search_stocks(q)
    return results