import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from datetime import datetime
import os
import asyncio

logger = logging.getLogger(__name__)

class WatchlistService:
    """
    Service for managing user watchlists with Supabase sync.
    
    Handles adding/removing stocks and crypto symbols from user watchlists
    and syncing data across devices through Supabase.
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("Supabase credentials not found in environment variables")
            self.supabase = None
        else:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
                self.supabase = None
    
    async def get_user_watchlist(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all symbols in user's watchlist with current market data.
        
        Args:
            user_id: User's UUID from Supabase auth
            
        Returns:
            List of watchlist entries with enriched market data
        """
        try:
            if not self.supabase:
                logger.warning("Supabase not available, returning mock watchlist")
                return self._get_mock_watchlist_data()
            
            # Check if we're using a mock user ID and return mock data instead of hitting Supabase
            if user_id == '12345678-1234-5678-9012-123456789012':
                logger.info("Using mock watchlist data for development user")
                return self._get_mock_watchlist_data()
            
            # Get watchlist items from Supabase
            result = self.supabase.table('watchlists') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('added_at', desc=True) \
                .execute()
            
            watchlist_items = result.data or []
            logger.info(f"Retrieved {len(watchlist_items)} watchlist items for user {user_id}")
            
            # Enrich with current market data
            enriched_items = []
            for item in watchlist_items:
                enriched_item = {
                    'id': item['id'],
                    'symbol': item['symbol'],
                    'symbol_type': item['symbol_type'],
                    'added_at': item['added_at']
                }
                
                # Get current market data for the symbol
                market_data = await self._get_market_data(item['symbol'], item['symbol_type'])
                if market_data:
                    enriched_item.update(market_data)
                else:
                    # Provide fallback data
                    enriched_item.update({
                        'name': item['symbol'],
                        'current_price': None,
                        'change_24h': None,
                        'change_percentage_24h': None,
                        'volume': None,
                        'market_cap': None
                    })
                
                enriched_items.append(enriched_item)
            
            return enriched_items
            
        except Exception as e:
            logger.error(f"Error retrieving watchlist for user {user_id}: {str(e)}")
            return self._get_mock_watchlist_data()
    
    async def add_to_watchlist(self, user_id: str, symbol: str, symbol_type: str) -> Dict[str, Any]:
        """
        Add a symbol to user's watchlist.
        
        Args:
            user_id: User's UUID
            symbol: Stock or crypto symbol (e.g., 'AAPL', 'BTC')
            symbol_type: 'stock' or 'crypto'
            
        Returns:
            Dictionary with success status and watchlist item
        """
        try:
            if not self.supabase or user_id == '12345678-1234-5678-9012-123456789012':
                # Mock behavior for development
                return {
                    'success': True,
                    'message': f'{symbol.upper()} added to watchlist (mock)',
                    'data': {'symbol': symbol.upper(), 'symbol_type': symbol_type}
                }
            
            # Validate symbol type
            if symbol_type not in ['stock', 'crypto']:
                return {
                    'success': False,
                    'message': 'Invalid symbol type. Must be "stock" or "crypto"',
                    'data': None
                }
            
            # Check if symbol already exists in watchlist
            existing = self.supabase.table('watchlists') \
                .select('id') \
                .eq('user_id', user_id) \
                .eq('symbol', symbol.upper()) \
                .execute()
            
            if existing.data:
                return {
                    'success': False,
                    'message': f'{symbol.upper()} is already in your watchlist',
                    'data': existing.data[0]
                }
            
            # Add to watchlist
            insert_data = {
                'user_id': user_id,
                'symbol': symbol.upper(),
                'symbol_type': symbol_type
            }
            
            result = self.supabase.table('watchlists') \
                .insert(insert_data) \
                .execute()
            
            if result.data:
                watchlist_item = result.data[0]
                
                # Get market data for the new item
                market_data = await self._get_market_data(symbol.upper(), symbol_type)
                if market_data:
                    watchlist_item.update(market_data)
                
                logger.info(f"Added {symbol.upper()} to watchlist for user {user_id}")
                return {
                    'success': True,
                    'message': f'{symbol.upper()} added to watchlist',
                    'data': watchlist_item
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to add symbol to watchlist',
                    'data': None
                }
                
        except Exception as e:
            logger.error(f"Error adding {symbol} to watchlist for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': 'Database error occurred',
                'data': None
            }
    
    async def remove_from_watchlist(self, user_id: str, symbol: str) -> Dict[str, Any]:
        """
        Remove a symbol from user's watchlist.
        
        Args:
            user_id: User's UUID
            symbol: Symbol to remove
            
        Returns:
            Dictionary with success status
        """
        try:
            if not self.supabase or user_id == '12345678-1234-5678-9012-123456789012':
                # Mock behavior for development
                return {
                    'success': True,
                    'message': f'{symbol.upper()} removed from watchlist (mock)'
                }
            
            result = self.supabase.table('watchlists') \
                .delete() \
                .eq('user_id', user_id) \
                .eq('symbol', symbol.upper()) \
                .execute()
            
            if result.data:
                logger.info(f"Removed {symbol.upper()} from watchlist for user {user_id}")
                return {
                    'success': True,
                    'message': f'{symbol.upper()} removed from watchlist'
                }
            else:
                return {
                    'success': False,
                    'message': 'Symbol not found in watchlist'
                }
                
        except Exception as e:
            logger.error(f"Error removing {symbol} from watchlist for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': 'Database error occurred'
            }
    
    async def get_watchlist_count(self, user_id: str) -> int:
        """Get the number of items in user's watchlist."""
        try:
            if not self.supabase or user_id == '12345678-1234-5678-9012-123456789012':
                return 4  # Mock count
            
            result = self.supabase.table('watchlists') \
                .select('id', count='exact') \
                .eq('user_id', user_id) \
                .execute()
            
            return result.count or 0
            
        except Exception as e:
            logger.error(f"Error getting watchlist count for user {user_id}: {str(e)}")
            return 0
    
    async def is_symbol_in_watchlist(self, user_id: str, symbol: str) -> bool:
        """Check if a symbol is in user's watchlist."""
        try:
            if not self.supabase or user_id == '12345678-1234-5678-9012-123456789012':
                return symbol.upper() in ['AAPL', 'MSFT', 'BTC', 'ETH']  # Mock data
            
            result = self.supabase.table('watchlists') \
                .select('id') \
                .eq('user_id', user_id) \
                .eq('symbol', symbol.upper()) \
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking if {symbol} is in watchlist for user {user_id}: {str(e)}")
            return False
    
    async def _get_market_data(self, symbol: str, symbol_type: str) -> Optional[Dict[str, Any]]:
        """Get current market data for a symbol."""
        try:
            if symbol_type == 'stock':
                return await self._get_stock_data(symbol)
            elif symbol_type == 'crypto':
                return await self._get_crypto_data(symbol)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return None
    
    async def _get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data using yfinance."""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            info = ticker.info
            
            if hist.empty:
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            prev_price = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
            change_24h = current_price - prev_price
            change_percentage_24h = (change_24h / prev_price) * 100 if prev_price != 0 else 0
            
            return {
                'name': info.get('longName', symbol),
                'current_price': current_price,
                'change_24h': change_24h,
                'change_percentage_24h': change_percentage_24h,
                'volume': float(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else None,
                'market_cap': info.get('marketCap'),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {str(e)}")
            return None
    
    async def _get_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get crypto data using CoinGecko API."""
        try:
            import httpx
            
            # Map common symbols to CoinGecko IDs
            crypto_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'USDT': 'tether',
                'BNB': 'binancecoin',
                'SOL': 'solana',
                'XRP': 'ripple',
                'USDC': 'usd-coin',
                'STETH': 'staked-ether',
                'ADA': 'cardano',
                'AVAX': 'avalanche-2'
            }
            
            coin_id = crypto_map.get(symbol.upper(), symbol.lower())
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.coingecko.com/api/v3/simple/price",
                    params={
                        'ids': coin_id,
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_market_cap': 'true',
                        'include_24hr_vol': 'true'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    coin_data = data.get(coin_id, {})
                    
                    if coin_data:
                        current_price = coin_data.get('usd', 0)
                        change_24h_pct = coin_data.get('usd_24h_change', 0)
                        change_24h = (current_price * change_24h_pct / 100) if change_24h_pct else 0
                        
                        return {
                            'name': symbol.upper(),
                            'current_price': current_price,
                            'change_24h': change_24h,
                            'change_percentage_24h': change_24h_pct,
                            'volume': coin_data.get('usd_24h_vol'),
                            'market_cap': coin_data.get('usd_market_cap'),
                            'last_updated': datetime.now().isoformat()
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting crypto data for {symbol}: {str(e)}")
            return None
    
    def _get_mock_watchlist_data(self) -> List[Dict[str, Any]]:
        """Return mock watchlist data when database is unavailable."""
        return [
            {
                'id': 'mock-1',
                'symbol': 'AAPL',
                'symbol_type': 'stock',
                'name': 'Apple Inc.',
                'current_price': 175.50,
                'change_24h': 2.30,
                'change_percentage_24h': 1.33,
                'volume': 45000000,
                'market_cap': 2750000000000,
                'added_at': '2024-01-01T10:00:00Z'
            },
            {
                'id': 'mock-2',
                'symbol': 'MSFT',
                'symbol_type': 'stock',
                'name': 'Microsoft Corporation',
                'current_price': 380.25,
                'change_24h': -1.50,
                'change_percentage_24h': -0.39,
                'volume': 25000000,
                'market_cap': 2800000000000,
                'added_at': '2024-01-01T11:00:00Z'
            },
            {
                'id': 'mock-3',
                'symbol': 'BTC',
                'symbol_type': 'crypto',
                'name': 'Bitcoin',
                'current_price': 45000.00,
                'change_24h': 1200.00,
                'change_percentage_24h': 2.74,
                'volume': 15000000000,
                'market_cap': 880000000000,
                'added_at': '2024-01-01T12:00:00Z'
            },
            {
                'id': 'mock-4',
                'symbol': 'ETH',
                'symbol_type': 'crypto',
                'name': 'Ethereum',
                'current_price': 2800.00,
                'change_24h': 45.00,
                'change_percentage_24h': 1.63,
                'volume': 8000000000,
                'market_cap': 336000000000,
                'added_at': '2024-01-01T13:00:00Z'
            }
        ]