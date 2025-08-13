# Trading Dashboard

A real-time financial market dashboard that aggregates stock prices, cryptocurrency data, news, and sentiment analysis in one place.

## Features

### Core Features
- 📈 **Real-time Market Data**: Track stocks and cryptocurrencies with live price updates
- 📰 **Financial News Aggregation**: Latest market news from multiple RSS feeds
- 💹 **Market Indices**: Monitor S&P 500, NASDAQ, DOW, VIX, Russell 2000, and more
- 🔐 **User Authentication**: Secure login with Supabase
- 💾 **Watchlist Management**: Save and track your favorite symbols with real-time prices

### Advanced Features (Phase 4)
- 🔍 **Advanced Sentiment Analysis**: 
  - Multi-source sentiment (Reddit r/wallstreetbets, StockTwits)
  - Real-time social media trending with WSB hot stocks
  - Bullish/bearish indicators with confidence scores
  - Combined sentiment from multiple sources
  - AI-powered rationale for sentiment classifications
- 📊 **Technical Analysis**:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Moving Averages (SMA 20, 50)
  - Bollinger Bands
  - Buy/Sell/Hold signals
- 🚀 **IPO Tracking**: Monitor upcoming and recent IPOs
- 📅 **Earnings Calendar**: Track upcoming earnings reports with estimates
- 💡 **Smart Tooltips**: 5 specialized tooltip types with rich information
- 🔄 **Real-time Updates**: Intelligent polling with connection monitoring
- 🤖 **AI-Powered Analysis**: TextBlob NLP with financial keyword detection

## Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Supabase** - Authentication and real-time data
- **Recharts** - Data visualization

### Backend
- **FastAPI** - Python web framework
- **yfinance** - Yahoo Finance data
- **CoinGecko API** - Cryptocurrency data
- **Redis** - Caching layer
- **BeautifulSoup4** - Web scraping
- **PRAW** - Reddit API wrapper
- **TextBlob** - Sentiment analysis
- **Celery** - Background task processing

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- Docker (for Redis)
- Supabase account

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/davidbennett1979/marketinfo.git
   cd marketinfo
   ```

2. **Set up Supabase**
   - Create a project at [supabase.com](https://supabase.com)
   - Run the SQL schema from `supabase/schema.sql`
   - Copy your project URL and keys

3. **Configure environment variables**

   Frontend (`frontend/.env.local`):
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
   ```

   Backend (`backend/.env`):
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_service_role_key
   REDIS_URL=redis://localhost:6379
   # Optional: Reddit API (for live sentiment)
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT=TradingDashboard/1.0
   # Optional: NewsAPI key
   NEWSAPI_KEY=your_newsapi_key
   ```

4. **Start Redis**
   ```bash
   docker-compose up -d
   ```

5. **Install and run the frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. **Install and run the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Endpoints

### Stock Data
- `GET /api/stocks/price/{symbol}` - Get current stock price
- `GET /api/stocks/indices` - Get major market indices
- `GET /api/stocks/history/{symbol}` - Get historical data

### Cryptocurrency Data
- `GET /api/crypto` - Get top 10 cryptocurrencies
- `GET /api/crypto/price/{coin_id}` - Get crypto price
- `GET /api/crypto/top/{limit}` - Get top cryptos by market cap
- `GET /api/crypto/history/{coin_id}` - Get historical data

### Sentiment Analysis
- `GET /api/sentiment/reddit/{subreddit}` - Get Reddit sentiment for a subreddit
- `GET /api/sentiment/reddit/wsb/trending` - Get trending posts from r/wallstreetbets
- `GET /api/sentiment/stocks/popular` - Get sentiment for popular stocks
- `GET /api/sentiment/stocks/wsb-trending` - Get WSB's most talked about stocks
- `GET /api/sentiment/stocktwits/{symbol}` - Get StockTwits sentiment
- `GET /api/sentiment/combined/{symbol}` - Get combined sentiment from all sources
- `POST /api/sentiment/analyze-text` - Analyze custom text sentiment

### Technical Analysis
- `GET /api/technical-analysis` - Get technical indicators for popular stocks
- `GET /api/technical-analysis/{symbol}` - Get technical indicators for a specific symbol

### News & Calendar
- `GET /api/news/latest` - Get latest financial news
- `GET /api/earnings/upcoming` - Get upcoming earnings calendar
- `GET /api/ipo/upcoming` - Get upcoming IPOs
- `GET /api/ipo/recent` - Get recent IPOs

### Watchlist
- `GET /api/watchlist` - Get user's watchlist
- `POST /api/watchlist` - Add symbol to watchlist
- `DELETE /api/watchlist/{symbol}` - Remove symbol from watchlist

## Development

### Project Structure
```
trading-dashboard/
├── frontend/           # Next.js frontend application
│   ├── app/           # App router pages
│   ├── components/    # React components
│   └── lib/          # Utilities and clients
├── backend/           # FastAPI backend application
│   ├── api/          # API endpoints
│   ├── services/     # Business logic
│   └── scrapers/     # Web scraping modules
└── supabase/         # Database schema and migrations
```

### Running Tests
```bash
# Frontend tests (when implemented)
cd frontend && npm test

# Backend tests (when implemented)
cd backend && pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) for stock market data
- [CoinGecko](https://www.coingecko.com/) for cryptocurrency data
- [Supabase](https://supabase.com/) for authentication and database
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework