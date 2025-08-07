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
    
    async def get_technical_indicators(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Calculate comprehensive technical indicators for a stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Dictionary containing all technical indicators and signals
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_technical"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_duration:
                    return cached_data
            
            logger.info(f"Calculating technical indicators for {symbol}")
            
            # Fetch stock data
            ticker = yf.Ticker(symbol)
            
            # Get 6 months of daily data for calculations
            hist = ticker.history(period="6mo")
            if hist.empty:
                logger.warning(f"No historical data available for {symbol}")
                return None
            
            info = ticker.info
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
            
            # Cache the result
            self.cache[cache_key] = (indicators, datetime.now().timestamp())
            
            logger.info(f"Successfully calculated technical indicators for {symbol}")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {str(e)}")
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
    
    def get_mock_technical_data(self) -> List[Dict[str, Any]]:
        """Return mock technical analysis data when API fails."""
        return [
            {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'rsi': 65.2,
                'macd': {
                    'macd': 2.45,
                    'signal': 1.89,
                    'histogram': 0.56
                },
                'sma_20': 175.80,
                'sma_50': 172.30,
                'bollinger_bands': {
                    'upper': 182.50,
                    'middle': 175.80,
                    'lower': 169.10
                },
                'current_price': 178.25,
                'signal': 'buy',
                'strength': 'moderate',
                'last_updated': datetime.now().isoformat()
            },
            {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'rsi': 58.7,
                'macd': {
                    'macd': 1.23,
                    'signal': 0.98,
                    'histogram': 0.25
                },
                'sma_20': 380.50,
                'sma_50': 375.20,
                'bollinger_bands': {
                    'upper': 395.20,
                    'middle': 380.50,
                    'lower': 365.80
                },
                'current_price': 382.15,
                'signal': 'hold',
                'strength': 'weak',
                'last_updated': datetime.now().isoformat()
            },
            {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc.',
                'rsi': 72.8,
                'macd': {
                    'macd': -0.85,
                    'signal': -0.45,
                    'histogram': -0.40
                },
                'sma_20': 142.60,
                'sma_50': 145.80,
                'bollinger_bands': {
                    'upper': 152.30,
                    'middle': 142.60,
                    'lower': 132.90
                },
                'current_price': 140.25,
                'signal': 'sell',
                'strength': 'strong',
                'last_updated': datetime.now().isoformat()
            },
            {
                'symbol': 'TSLA',
                'name': 'Tesla Inc.',
                'rsi': 45.3,
                'macd': {
                    'macd': -2.15,
                    'signal': -1.80,
                    'histogram': -0.35
                },
                'sma_20': 245.80,
                'sma_50': 250.30,
                'bollinger_bands': {
                    'upper': 265.20,
                    'middle': 245.80,
                    'lower': 226.40
                },
                'current_price': 242.50,
                'signal': 'buy',
                'strength': 'strong',
                'last_updated': datetime.now().isoformat()
            },
            {
                'symbol': 'AMZN',
                'name': 'Amazon.com Inc.',
                'rsi': 52.1,
                'macd': {
                    'macd': 0.75,
                    'signal': 0.60,
                    'histogram': 0.15
                },
                'sma_20': 156.20,
                'sma_50': 155.80,
                'bollinger_bands': {
                    'upper': 165.40,
                    'middle': 156.20,
                    'lower': 147.00
                },
                'current_price': 157.85,
                'signal': 'hold',
                'strength': 'moderate',
                'last_updated': datetime.now().isoformat()
            },
            {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation',
                'rsi': 69.5,
                'macd': {
                    'macd': 3.25,
                    'signal': 2.80,
                    'histogram': 0.45
                },
                'sma_20': 891.30,
                'sma_50': 865.20,
                'bollinger_bands': {
                    'upper': 950.20,
                    'middle': 891.30,
                    'lower': 832.40
                },
                'current_price': 905.75,
                'signal': 'buy',
                'strength': 'moderate',
                'last_updated': datetime.now().isoformat()
            },
            {
                'symbol': 'META',
                'name': 'Meta Platforms Inc.',
                'rsi': 41.8,
                'macd': {
                    'macd': -1.45,
                    'signal': -1.20,
                    'histogram': -0.25
                },
                'sma_20': 528.90,
                'sma_50': 535.60,
                'bollinger_bands': {
                    'upper': 555.80,
                    'middle': 528.90,
                    'lower': 502.00
                },
                'current_price': 525.40,
                'signal': 'hold',
                'strength': 'weak',
                'last_updated': datetime.now().isoformat()
            },
            {
                'symbol': 'NFLX',
                'name': 'Netflix Inc.',
                'rsi': 33.2,
                'macd': {
                    'macd': -2.80,
                    'signal': -2.45,
                    'histogram': -0.35
                },
                'sma_20': 598.20,
                'sma_50': 615.40,
                'bollinger_bands': {
                    'upper': 645.80,
                    'middle': 598.20,
                    'lower': 550.60
                },
                'current_price': 585.30,
                'signal': 'buy',
                'strength': 'strong',
                'last_updated': datetime.now().isoformat()
            }
        ]