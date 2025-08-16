"""
Trading Dashboard API - Main Application Entry Point

This FastAPI application provides a comprehensive REST API for financial data
aggregation, including stock prices, cryptocurrency data, sentiment analysis,
earnings calendars, IPO tracking, and technical analysis.

Features:
- Real-time market data from yfinance and CoinGecko
- Social sentiment analysis from Reddit and StockTwits
- Technical indicators (RSI, MACD, Bollinger Bands)
- User watchlist management with Supabase
- Earnings and IPO calendars with web scraping
- Caching layer for performance optimization

Author: David Bennett
Version: 1.0.0
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys
import logging

# Add the current directory to Python path for relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure structured logging for better debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
load_dotenv()

# Create FastAPI application with comprehensive metadata
app = FastAPI(
    title="Trading Dashboard API",
    description="Real-time financial market data aggregation and analysis API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc documentation
)

# Configure CORS middleware to allow frontend access
# Note: In production, replace with specific domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from api.stocks import router as stocks_router
from api.crypto import router as crypto_router
from api.news import router as news_router
from api.sentiment import router as sentiment_router
from api.ipo import router as ipo_router
from api.earnings import router as earnings_router
from api.watchlist import router as watchlist_router
from api.technical_analysis import router as technical_router
from api.ai_chat import router as ai_chat_router
from api.system import router as system_router

app.include_router(stocks_router)
app.include_router(crypto_router)
app.include_router(news_router)
app.include_router(sentiment_router)
app.include_router(ipo_router)
app.include_router(earnings_router)
app.include_router(watchlist_router)
app.include_router(technical_router)
app.include_router(ai_chat_router)
app.include_router(system_router)

@app.get("/")
async def root():
    return {"message": "Trading Dashboard API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint works"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)