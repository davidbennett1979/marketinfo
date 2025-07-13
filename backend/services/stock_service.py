import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import time

logger = logging.getLogger(__name__)

class StockService:
    """Service for fetching stock data using yfinance"""
    
    @staticmethod
    def get_stock_price(symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price and daily change"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Use history method which is more reliable
            hist = ticker.history(period="5d")
            if hist.empty:
                logger.error(f"No data found for symbol {symbol}")
                return None
            
            # Get the latest price
            current_price = float(hist['Close'].iloc[-1])
            
            # Get previous close (if we have at least 2 days of data)
            if len(hist) >= 2:
                previous_close = float(hist['Close'].iloc[-2])
            else:
                previous_close = current_price
            
            # Calculate daily change
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            # Get high/low/volume from today's data
            today_data = hist.iloc[-1]
            
            # Try to get company info with minimal API calls
            try:
                info = ticker.info
                name = info.get('longName') or info.get('shortName') or symbol
                market_cap = info.get('marketCap', 0)
            except:
                name = symbol
                market_cap = 0
            
            return {
                'symbol': symbol.upper(),
                'name': name,
                'current_price': round(current_price, 2),
                'previous_close': round(previous_close, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'volume': int(today_data.get('Volume', 0)),
                'market_cap': market_cap,
                'high': round(float(today_data.get('High', current_price)), 2),
                'low': round(float(today_data.get('Low', current_price)), 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    def get_multiple_stocks(symbols: List[str]) -> List[Dict[str, Any]]:
        """Get price data for multiple stocks"""
        results = []
        for i, symbol in enumerate(symbols):
            if i > 0:
                time.sleep(0.5)  # Small delay to avoid rate limiting
            data = StockService.get_stock_price(symbol)
            if data:
                results.append(data)
        return results
    
    @staticmethod
    def get_market_indices() -> List[Dict[str, Any]]:
        """Get major market indices"""
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^RUT': 'Russell 2000',
            '^VIX': 'VIX'
        }
        
        results = []
        for symbol, name in indices.items():
            data = StockService.get_stock_price(symbol)
            if data:
                data['name'] = name
                data['symbol_type'] = 'index'
                results.append(data)
        
        return results
    
    @staticmethod
    def get_historical_data(symbol: str, period: str = "1mo") -> Optional[Dict[str, Any]]:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            # Convert to list of dicts for easier JSON serialization
            history_data = []
            for date, row in hist.iterrows():
                history_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume'])
                })
            
            return {
                'symbol': symbol.upper(),
                'period': period,
                'data': history_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    def search_stocks(query: str) -> List[Dict[str, str]]:
        """Search for stocks by symbol or name"""
        try:
            # For now, we'll use a predefined list of popular stocks
            # In production, you might want to use a more comprehensive API
            popular_stocks = {
                'AAPL': 'Apple Inc.',
                'MSFT': 'Microsoft Corporation',
                'GOOGL': 'Alphabet Inc.',
                'AMZN': 'Amazon.com Inc.',
                'TSLA': 'Tesla Inc.',
                'META': 'Meta Platforms Inc.',
                'NVDA': 'NVIDIA Corporation',
                'JPM': 'JPMorgan Chase & Co.',
                'V': 'Visa Inc.',
                'JNJ': 'Johnson & Johnson'
            }
            
            query_lower = query.lower()
            results = []
            
            for symbol, name in popular_stocks.items():
                if query_lower in symbol.lower() or query_lower in name.lower():
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'type': 'stock'
                    })
            
            return results[:10]  # Limit to 10 results
            
        except Exception as e:
            logger.error(f"Error searching stocks: {str(e)}")
            return []