from fastapi import APIRouter, HTTPException
from typing import List, Optional
from services.crypto_service import CryptoService
from services.cache_service import CacheService

router = APIRouter(prefix="/api/crypto", tags=["crypto"])
cache = CacheService()

@router.get("/price/{coin_id}")
async def get_crypto_price(coin_id: str):
    """Get current crypto price"""
    # Check cache first
    cached_data = cache.get_crypto_price(coin_id)
    if cached_data:
        return cached_data
    
    # Fetch fresh data
    crypto_service = CryptoService()
    try:
        data = await crypto_service.get_crypto_price(coin_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Crypto {coin_id} not found")
        
        # Cache the result
        cache.set_crypto_price(coin_id, data)
        return data
    finally:
        await crypto_service.close()

@router.get("/top/{limit}")
async def get_top_cryptos(limit: int = 20):
    """Get top cryptocurrencies by market cap"""
    cache_key = f"crypto:top:{limit}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Fetch fresh data
    crypto_service = CryptoService()
    try:
        data = await crypto_service.get_top_cryptos(limit)
        
        # Cache the result
        cache.set(cache_key, data, 'crypto_price')
        return data
    finally:
        await crypto_service.close()

@router.get("/history/{coin_id}")
async def get_crypto_history(coin_id: str, days: int = 30):
    """Get historical crypto data"""
    cache_key = f"crypto:history:{coin_id}:{days}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Fetch fresh data
    crypto_service = CryptoService()
    try:
        data = await crypto_service.get_crypto_history(coin_id, days)
        if not data:
            raise HTTPException(status_code=404, detail=f"Historical data for {coin_id} not found")
        
        # Cache the result
        cache.set(cache_key, data, 'historical')
        return data
    finally:
        await crypto_service.close()

@router.get("/search")
async def search_cryptos(q: str):
    """Search for cryptocurrencies"""
    if len(q) < 1:
        return []
    
    crypto_service = CryptoService()
    try:
        results = await crypto_service.search_cryptos(q)
        return results
    finally:
        await crypto_service.close()

@router.get("/convert/{symbol}")
async def convert_symbol_to_id(symbol: str):
    """Convert crypto symbol to CoinGecko ID"""
    symbol = symbol.upper()
    mapping = CryptoService.SYMBOL_TO_ID
    
    if symbol in mapping:
        return {"symbol": symbol, "id": mapping[symbol]}
    else:
        return {"symbol": symbol, "id": symbol.lower()}