-- Trading Dashboard Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Watchlists table (user's watched symbols)
CREATE TABLE watchlists (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    symbol_type VARCHAR(10) NOT NULL CHECK (symbol_type IN ('stock', 'crypto')),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, symbol)
);

-- User preferences table
CREATE TABLE user_preferences (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    theme VARCHAR(10) DEFAULT 'light' CHECK (theme IN ('light', 'dark')),
    email_notifications BOOLEAN DEFAULT true,
    default_currency VARCHAR(3) DEFAULT 'USD',
    refresh_interval INTEGER DEFAULT 300, -- seconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cached stock/crypto data table
CREATE TABLE cached_market_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    symbol_type VARCHAR(10) NOT NULL CHECK (symbol_type IN ('stock', 'crypto', 'index')),
    name VARCHAR(255),
    current_price DECIMAL(20, 8),
    change_24h DECIMAL(10, 2),
    change_percentage_24h DECIMAL(10, 2),
    volume DECIMAL(20, 2),
    market_cap DECIMAL(20, 2),
    high_24h DECIMAL(20, 8),
    low_24h DECIMAL(20, 8),
    data JSONB, -- Additional data like fundamentals
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, symbol_type)
);

-- News articles table
CREATE TABLE news_articles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title TEXT NOT NULL,
    source VARCHAR(255) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    author VARCHAR(255),
    description TEXT,
    content TEXT,
    sentiment_score DECIMAL(3, 2) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    related_symbols TEXT[], -- Array of related stock/crypto symbols
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trade recommendations table
CREATE TABLE trade_recommendations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    symbol_type VARCHAR(10) NOT NULL CHECK (symbol_type IN ('stock', 'crypto')),
    action VARCHAR(10) NOT NULL CHECK (action IN ('buy', 'sell', 'hold')),
    confidence_score DECIMAL(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    reasoning TEXT,
    target_price DECIMAL(20, 8),
    stop_loss DECIMAL(20, 8),
    algorithm_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Earnings calendar table
CREATE TABLE earnings_calendar (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    earnings_date DATE NOT NULL,
    earnings_time VARCHAR(20), -- 'before_open', 'after_close', 'during_market'
    estimated_eps DECIMAL(10, 4),
    previous_eps DECIMAL(10, 4),
    estimated_revenue DECIMAL(20, 2),
    previous_revenue DECIMAL(20, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, earnings_date)
);

-- IPO calendar table
CREATE TABLE ipo_calendar (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(10),
    company_name VARCHAR(255) NOT NULL,
    ipo_date DATE NOT NULL,
    price_range_low DECIMAL(10, 2),
    price_range_high DECIMAL(10, 2),
    shares_offered BIGINT,
    lead_underwriter VARCHAR(255),
    exchange VARCHAR(50),
    industry VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_name, ipo_date)
);

-- Social sentiment data table
CREATE TABLE social_sentiment (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    source VARCHAR(50) NOT NULL, -- 'reddit', 'twitter', 'stocktwits'
    sentiment_score DECIMAL(3, 2) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    bullish_count INTEGER DEFAULT 0,
    bearish_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    total_mentions INTEGER DEFAULT 0,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, source, period_start, period_end)
);

-- Create indexes for better query performance
CREATE INDEX idx_watchlists_user_id ON watchlists(user_id);
CREATE INDEX idx_cached_market_data_symbol ON cached_market_data(symbol, symbol_type);
CREATE INDEX idx_cached_market_data_updated ON cached_market_data(last_updated);
CREATE INDEX idx_news_articles_published ON news_articles(published_at DESC);
CREATE INDEX idx_news_articles_symbols ON news_articles USING GIN(related_symbols);
CREATE INDEX idx_trade_recommendations_created ON trade_recommendations(created_at DESC);
CREATE INDEX idx_earnings_calendar_date ON earnings_calendar(earnings_date);
CREATE INDEX idx_social_sentiment_symbol ON social_sentiment(symbol, period_end DESC);

-- Create update trigger for user_preferences
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE
    ON user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE cached_market_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE earnings_calendar ENABLE ROW LEVEL SECURITY;
ALTER TABLE ipo_calendar ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_sentiment ENABLE ROW LEVEL SECURITY;

-- Watchlists policies (users can only see/modify their own watchlists)
CREATE POLICY "Users can view own watchlists" ON watchlists
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own watchlists" ON watchlists
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own watchlists" ON watchlists
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own watchlists" ON watchlists
    FOR DELETE USING (auth.uid() = user_id);

-- User preferences policies
CREATE POLICY "Users can view own preferences" ON user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences" ON user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences" ON user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

-- Public read access for market data tables
CREATE POLICY "Anyone can view market data" ON cached_market_data
    FOR SELECT USING (true);

CREATE POLICY "Anyone can view news" ON news_articles
    FOR SELECT USING (true);

CREATE POLICY "Anyone can view recommendations" ON trade_recommendations
    FOR SELECT USING (true);

CREATE POLICY "Anyone can view earnings calendar" ON earnings_calendar
    FOR SELECT USING (true);

CREATE POLICY "Anyone can view IPO calendar" ON ipo_calendar
    FOR SELECT USING (true);

CREATE POLICY "Anyone can view social sentiment" ON social_sentiment
    FOR SELECT USING (true);

-- Service role policies for backend to insert/update data
-- Note: These will work with the service_role key from the backend
CREATE POLICY "Service role can insert market data" ON cached_market_data
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can update market data" ON cached_market_data
    FOR UPDATE USING (true);

CREATE POLICY "Service role can insert news" ON news_articles
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can insert recommendations" ON trade_recommendations
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can insert earnings" ON earnings_calendar
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can update earnings" ON earnings_calendar
    FOR UPDATE USING (true);

CREATE POLICY "Service role can insert IPOs" ON ipo_calendar
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can insert sentiment" ON social_sentiment
    FOR INSERT WITH CHECK (true);