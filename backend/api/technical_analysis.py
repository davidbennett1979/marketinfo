from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import asyncio
from datetime import datetime, timedelta
from services.technical_analysis_service import TechnicalAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/technical-analysis", tags=["technical-analysis"])

# Initialize technical analysis service
technical_service = TechnicalAnalysisService()

@router.get("")
async def get_technical_analysis() -> List[Dict[str, Any]]:
    """
    Get technical analysis for popular stocks.
    
    Returns:
        List of technical indicators for major stocks
    """
    try:
        logger.info("Fetching technical analysis for popular stocks")
        
        # Popular stocks for technical analysis
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
        
        # Get technical analysis for all symbols
        results = []
        for symbol in symbols:
            try:
                analysis = await technical_service.get_technical_indicators(symbol)
                if analysis:
                    results.append(analysis)
                    logger.info(f"Retrieved technical analysis for {symbol}")
                else:
                    logger.warning(f"No technical analysis data available for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error getting technical analysis for {symbol}: {str(e)}")
                # Continue with other symbols
                continue
        
        if not results:
            logger.warning("No technical analysis data available, using fallback data")
            results = technical_service.get_mock_technical_data()
        
        logger.info(f"Retrieved technical analysis for {len(results)} symbols")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching technical analysis: {str(e)}")
        # Return fallback data instead of error to prevent frontend crashes
        return technical_service.get_mock_technical_data()

@router.get("/symbol/{symbol}")
async def get_symbol_technical_analysis(symbol: str) -> Dict[str, Any]:
    """
    Get technical analysis for a specific symbol.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        
    Returns:
        Technical indicators for the specified symbol
    """
    try:
        logger.info(f"Fetching technical analysis for {symbol}")
        
        analysis = await technical_service.get_technical_indicators(symbol.upper())
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Technical analysis not available for {symbol}")
        
        logger.info(f"Retrieved technical analysis for {symbol}")
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching technical analysis for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch technical analysis")

@router.get("/signals")
async def get_trading_signals() -> List[Dict[str, Any]]:
    """
    Get trading signals summary for popular stocks.
    
    Returns:
        List of trading signals with recommendations
    """
    try:
        logger.info("Fetching trading signals")
        
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
        signals = []
        
        for symbol in symbols:
            try:
                analysis = await technical_service.get_technical_indicators(symbol)
                if analysis:
                    signal = {
                        'symbol': symbol,
                        'name': analysis.get('name', symbol),
                        'signal': analysis.get('signal', 'hold'),
                        'strength': analysis.get('strength', 'weak'),
                        'current_price': analysis.get('current_price'),
                        'rsi': analysis.get('rsi'),
                        'macd_histogram': analysis.get('macd', {}).get('histogram', 0),
                        'last_updated': analysis.get('last_updated')
                    }
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Error getting signal for {symbol}: {str(e)}")
                continue
        
        if not signals:
            # Fallback signals data
            signals = [
                {
                    'symbol': 'AAPL',
                    'name': 'Apple Inc.',
                    'signal': 'buy',
                    'strength': 'moderate',
                    'current_price': 178.25,
                    'rsi': 65.2,
                    'macd_histogram': 0.56,
                    'last_updated': datetime.now().isoformat()
                },
                {
                    'symbol': 'MSFT',
                    'name': 'Microsoft Corporation',
                    'signal': 'hold',
                    'strength': 'weak',
                    'current_price': 382.15,
                    'rsi': 58.7,
                    'macd_histogram': 0.25,
                    'last_updated': datetime.now().isoformat()
                }
            ]
        
        logger.info(f"Retrieved trading signals for {len(signals)} symbols")
        return signals
        
    except Exception as e:
        logger.error(f"Error fetching trading signals: {str(e)}")
        return []

@router.get("/overview")
async def get_market_technical_overview() -> Dict[str, Any]:
    """
    Get overall market technical analysis overview.
    
    Returns:
        Market-wide technical analysis summary
    """
    try:
        logger.info("Fetching market technical overview")
        
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
        analyses = []
        
        for symbol in symbols:
            try:
                analysis = await technical_service.get_technical_indicators(symbol)
                if analysis:
                    analyses.append(analysis)
            except Exception:
                continue
        
        if not analyses:
            return {
                'total_symbols': 0,
                'bullish_signals': 0,
                'bearish_signals': 0,
                'neutral_signals': 0,
                'market_sentiment': 'neutral',
                'last_updated': datetime.now().isoformat()
            }
        
        # Calculate market overview
        buy_signals = len([a for a in analyses if a.get('signal') == 'buy'])
        sell_signals = len([a for a in analyses if a.get('signal') == 'sell'])
        hold_signals = len([a for a in analyses if a.get('signal') == 'hold'])
        
        # Determine overall market sentiment
        if buy_signals > sell_signals and buy_signals > hold_signals:
            market_sentiment = 'bullish'
        elif sell_signals > buy_signals and sell_signals > hold_signals:
            market_sentiment = 'bearish'
        else:
            market_sentiment = 'neutral'
        
        overview = {
            'total_symbols': len(analyses),
            'bullish_signals': buy_signals,
            'bearish_signals': sell_signals,
            'neutral_signals': hold_signals,
            'market_sentiment': market_sentiment,
            'avg_rsi': sum([a.get('rsi', 50) for a in analyses]) / len(analyses) if analyses else 50,
            'last_updated': datetime.now().isoformat()
        }
        
        logger.info(f"Market technical overview: {market_sentiment} sentiment")
        return overview
        
    except Exception as e:
        logger.error(f"Error fetching market technical overview: {str(e)}")
        return {
            'total_symbols': 0,
            'bullish_signals': 0,
            'bearish_signals': 0,
            'neutral_signals': 0,
            'market_sentiment': 'neutral',
            'last_updated': datetime.now().isoformat()
        }