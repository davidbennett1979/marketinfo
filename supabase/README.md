# Supabase Database Setup

## How to Apply the Schema

1. **Go to your Supabase Dashboard**
   - Navigate to https://app.supabase.com
   - Select your project

2. **Open the SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Run the Schema**
   - Copy the entire contents of `schema.sql`
   - Paste it into the SQL editor
   - Click "Run" or press Cmd/Ctrl + Enter

## Tables Created

### User Data
- `watchlists` - User's watched stocks/crypto
- `user_preferences` - User settings and preferences

### Market Data
- `cached_market_data` - Cached price data for stocks/crypto
- `news_articles` - Financial news articles
- `trade_recommendations` - AI-generated trade suggestions
- `earnings_calendar` - Upcoming earnings reports
- `ipo_calendar` - Upcoming IPOs
- `social_sentiment` - Reddit/Twitter sentiment data

## Row Level Security (RLS)

The schema includes RLS policies:
- **Personal data** (watchlists, preferences): Users can only access their own data
- **Market data**: Public read access for all authenticated users
- **Backend writes**: The service role key can insert/update market data

## Testing the Setup

After running the schema, test it:

1. Go to "Table Editor" in Supabase
2. You should see all 8 tables listed
3. Try inserting a test record in `watchlists` table
4. Verify RLS is working by checking the "Authentication" column

## Next Steps

1. The backend will use the `service_role` key to insert market data
2. The frontend will use the `anon` key for user-specific operations
3. Real-time subscriptions can be set up for live data updates