import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CryptoService:
    """Service for fetching cryptocurrency data using CoinGecko API"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_crypto_price(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Get current crypto price and 24h change"""
        try:
            # CoinGecko uses IDs like 'bitcoin', 'ethereum' instead of symbols
            url = f"{self.BASE_URL}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if coin_id not in data:
                return None
            
            coin_data = data[coin_id]
            
            return {
                'symbol': coin_id.upper(),
                'name': coin_id.title(),
                'current_price': coin_data.get('usd'),
                'change_24h': coin_data.get('usd_24h_change'),
                'volume_24h': coin_data.get('usd_24h_vol'),
                'market_cap': coin_data.get('usd_market_cap'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching crypto data for {coin_id}: {str(e)}")
            return None
    
    async def get_top_cryptos(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top cryptocurrencies by market cap"""
        try:
            url = f"{self.BASE_URL}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': False
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for coin in data:
                results.append({
                    'symbol': coin['symbol'].upper(),
                    'name': coin['name'],
                    'current_price': coin['current_price'],
                    'change_24h': coin['price_change_24h'],
                    'change_percent_24h': coin['price_change_percentage_24h'],
                    'volume_24h': coin['total_volume'],
                    'market_cap': coin['market_cap'],
                    'rank': coin['market_cap_rank'],
                    'image': coin.get('image'),
                    'timestamp': datetime.now().isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching top cryptos: {str(e)}")
            return []
    
    async def get_crypto_history(self, coin_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get historical price data for a cryptocurrency"""
        try:
            url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert timestamp to readable date
            history_data = []
            for price_point in data['prices']:
                timestamp, price = price_point
                date = datetime.fromtimestamp(timestamp / 1000)
                history_data.append({
                    'date': date.strftime('%Y-%m-%d %H:%M'),
                    'price': round(price, 2)
                })
            
            return {
                'coin_id': coin_id,
                'days': days,
                'data': history_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching crypto history for {coin_id}: {str(e)}")
            return None
    
    async def search_cryptos(self, query: str) -> List[Dict[str, str]]:
        """Search for cryptocurrencies"""
        try:
            url = f"{self.BASE_URL}/search"
            params = {'query': query}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for coin in data.get('coins', [])[:10]:  # Limit to 10 results
                results.append({
                    'id': coin['id'],
                    'symbol': coin['symbol'].upper(),
                    'name': coin['name'],
                    'type': 'crypto'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching cryptos: {str(e)}")
            return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    # Common crypto ID mappings
    SYMBOL_TO_ID = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'SOL': 'solana',
        'XRP': 'ripple',
        'USDT': 'tether',
        'USDC': 'usd-coin',
        'ADA': 'cardano',
        'AVAX': 'avalanche-2',
        'DOGE': 'dogecoin'
    }