# Trading Dashboard

A real-time financial market dashboard that aggregates stock prices, cryptocurrency data, news, and sentiment analysis in one place.

## Features

- 📈 **Real-time Market Data**: Track stocks and cryptocurrencies with live price updates
- 📰 **Financial News Aggregation**: Latest market news from multiple sources
- 💹 **Market Indices**: Monitor S&P 500, NASDAQ, DOW, and more
- 🔍 **Sentiment Analysis**: Social media sentiment from Reddit and Twitter
- 📊 **Interactive Charts**: Historical price data visualization
- 🔐 **User Authentication**: Secure login with Supabase
- 💾 **Watchlist**: Save and track your favorite symbols

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
- `GET /api/crypto/price/{coin_id}` - Get crypto price
- `GET /api/crypto/top/{limit}` - Get top cryptos by market cap
- `GET /api/crypto/history/{coin_id}` - Get historical data

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