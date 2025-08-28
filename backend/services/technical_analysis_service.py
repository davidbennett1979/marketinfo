import logging
from typing import Dict, Any, Optional, List
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class TechnicalAnalysisService:
    """
    Service for calculating technical indicators and trading signals.
    
    Provides RSI, MACD, moving averages, Bollinger Bands, and other
    technical analysis indicators for stocks.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        self.max_cache_size = 128   # prevent unbounded growth

    def _evict_if_needed(self):
        """Evict least-recent entry when cache exceeds max size."""
        try:
            if len(self.cache) <= self.max_cache_size:
                return
            # Find oldest by timestamp
            oldest_key = None
            oldest_ts = None
            for k, (_, ts) in self.cache.items():
                if oldest_ts is None or ts < oldest_ts:
                    oldest_key = k
                    oldest_ts = ts
            if oldest_key is not None:
                self.cache.pop(oldest_key, None)
        except Exception:
            # On any error, clear half the cache as a safe fallback
            try:
                for i, k in enumerate(list(self.cache.keys())):
                    if i % 2 == 0:
                        self.cache.pop(k, None)
            except Exception:
                self.cache = {}
    
    async def get_technical_indicators(self, symbol: str, retry_count: int = 3) -> Optional[Dict[str, Any]]:
        """
        Calculate comprehensive technical indicators for a stock symbol with retry logic.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            retry_count: Number of retries on failure
            
        Returns:
            Dictionary containing all technical indicators and signals
        """
        # Check Redis cache first
        try:
            from services.cache_service import CacheService
            redis_cache = CacheService()
            redis_key = f"technical:{symbol}"
            cached_data = redis_cache.get(redis_key)
            if cached_data:
                logger.debug(f"Returning Redis-cached technical indicators for {symbol}")
                return cached_data
        except Exception as e:
            logger.debug(f"Redis cache check failed: {e}")
        
        # Check in-memory cache
        cache_key = f"{symbol}_technical"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_duration:
                return cached_data
        
        # Try multiple times with exponential backoff
        for attempt in range(retry_count):
            try:
                logger.info(f"Calculating technical indicators for {symbol} (attempt {attempt + 1}/{retry_count})")
                
                # Fetch stock data with timeout
                # Get 6 months of daily data for calculations without blocking the event loop
                def _fetch_hist_sync():
                    return yf.Ticker(symbol).history(period="6mo")

                try:
                    hist = await asyncio.wait_for(asyncio.to_thread(_fetch_hist_sync), timeout=15)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout fetching historical data for {symbol}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None
                if hist.empty:
                    logger.warning(f"No historical data available for {symbol}")
                    if attempt < retry_count - 1:
                        import asyncio
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                        continue
                    return None
                
                # Fetch info lazily; if it fails, fall back to symbol
                try:
                    info = yf.Ticker(symbol).info
                except Exception:
                    info = {}
                current_price = float(hist['Close'].iloc[-1])
                
                # Calculate technical indicators
                indicators = {
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'current_price': current_price,
                    'last_updated': datetime.now().isoformat()
                }
                
                # RSI (Relative Strength Index)
                rsi = self._calculate_rsi(hist['Close'])
                indicators['rsi'] = rsi
                
                # MACD
                macd_data = self._calculate_macd(hist['Close'])
                indicators['macd'] = macd_data
                
                # Moving Averages
                sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
                sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
                indicators['sma_20'] = float(sma_20) if not pd.isna(sma_20) else current_price
                indicators['sma_50'] = float(sma_50) if not pd.isna(sma_50) else current_price
                
                # Bollinger Bands
                bollinger = self._calculate_bollinger_bands(hist['Close'])
                indicators['bollinger_bands'] = bollinger
                
                # Generate trading signal
                signal_data = self._generate_trading_signal(indicators)
                indicators.update(signal_data)
                
                # Cache the result in both memory and Redis
                self.cache[cache_key] = (indicators, datetime.now().timestamp())
                self._evict_if_needed()
                
                # Also cache in Redis for 15 minutes
                try:
                    redis_cache.set(redis_key, indicators, 'technical', custom_ttl=900)
                except Exception as e:
                    logger.debug(f"Redis cache set failed: {e}")
                
                logger.info(f"Successfully calculated technical indicators for {symbol}")
                return indicators
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {str(e)}")
                if attempt < retry_count - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All {retry_count} attempts failed for {symbol}")
                    return None
        
        logger.error(f"All {retry_count} attempts failed for {symbol}")
        return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return 50.0
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        try:
            exp1 = prices.ewm(span=fast).mean()
            exp2 = prices.ewm(span=slow).mean()
            macd = exp1 - exp2
            macd_signal = macd.ewm(span=signal).mean()
            histogram = macd - macd_signal
            
            return {
                'macd': float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0.0,
                'signal': float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else 0.0,
                'histogram': float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands."""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            return {
                'upper': float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else prices.iloc[-1] * 1.1,
                'middle': float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else prices.iloc[-1],
                'lower': float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else prices.iloc[-1] * 0.9
            }
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            current_price = float(prices.iloc[-1])
            return {
                'upper': current_price * 1.1,
                'middle': current_price,
                'lower': current_price * 0.9
            }
    
    def _generate_trading_signal(self, indicators: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate trading signal based on multiple technical indicators.
        
        Args:
            indicators: Dictionary containing all technical indicators
            
        Returns:
            Dictionary with signal ('buy', 'sell', 'hold') and strength ('strong', 'moderate', 'weak')
        """
        try:
            signals = []
            current_price = indicators['current_price']
            rsi = indicators['rsi']
            macd = indicators['macd']
            sma_20 = indicators['sma_20']
            sma_50 = indicators['sma_50']
            bollinger = indicators['bollinger_bands']
            
            # RSI signals
            if rsi <= 30:
                signals.append(('buy', 'strong'))
            elif rsi <= 40:
                signals.append(('buy', 'moderate'))
            elif rsi >= 70:
                signals.append(('sell', 'strong'))
            elif rsi >= 60:
                signals.append(('sell', 'moderate'))
            else:
                signals.append(('hold', 'weak'))
            
            # MACD signals
            macd_histogram = macd['histogram']
            if macd_histogram > 0 and macd['macd'] > macd['signal']:
                signals.append(('buy', 'moderate'))
            elif macd_histogram < 0 and macd['macd'] < macd['signal']:
                signals.append(('sell', 'moderate'))
            else:
                signals.append(('hold', 'weak'))
            
            # Moving Average signals
            if current_price > sma_20 > sma_50:
                signals.append(('buy', 'moderate'))
            elif current_price < sma_20 < sma_50:
                signals.append(('sell', 'moderate'))
            else:
                signals.append(('hold', 'weak'))
            
            # Bollinger Bands signals
            if current_price < bollinger['lower']:
                signals.append(('buy', 'strong'))
            elif current_price > bollinger['upper']:
                signals.append(('sell', 'strong'))
            else:
                signals.append(('hold', 'weak'))
            
            # Aggregate signals
            buy_count = len([s for s in signals if s[0] == 'buy'])
            sell_count = len([s for s in signals if s[0] == 'sell'])
            hold_count = len([s for s in signals if s[0] == 'hold'])
            
            # Determine overall signal
            if buy_count > sell_count and buy_count > hold_count:
                overall_signal = 'buy'
            elif sell_count > buy_count and sell_count > hold_count:
                overall_signal = 'sell'
            else:
                overall_signal = 'hold'
            
            # Determine signal strength
            strong_signals = len([s for s in signals if s[1] == 'strong'])
            moderate_signals = len([s for s in signals if s[1] == 'moderate'])
            
            if strong_signals >= 2:
                signal_strength = 'strong'
            elif strong_signals >= 1 or moderate_signals >= 2:
                signal_strength = 'moderate'
            else:
                signal_strength = 'weak'
            
            return {
                'signal': overall_signal,
                'strength': signal_strength
            }
            
        except Exception as e:
            logger.error(f"Error generating trading signal: {str(e)}")
            return {'signal': 'hold', 'strength': 'weak'}
    
