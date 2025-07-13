import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import MarketIndices from '@/components/dashboard/MarketIndices'
import CryptoTracker from '@/components/dashboard/CryptoTracker'
import NewsFeed from '@/components/dashboard/NewsFeed'
import StockCard from '@/components/dashboard/StockCard'

export default async function DashboardPage() {
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Popular stocks to display
  const watchlistStocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Trading Dashboard</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Market Data */}
          <div className="lg:col-span-2 space-y-6">
            {/* Market Indices */}
            <MarketIndices />

            {/* Watchlist Stocks */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Watchlist</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {watchlistStocks.map((symbol) => (
                  <StockCard key={symbol} symbol={symbol} />
                ))}
              </div>
            </div>

            {/* Crypto Tracker */}
            <CryptoTracker />
          </div>

          {/* Right Column - News */}
          <div className="space-y-6">
            <NewsFeed />
            
            {/* Earnings Calendar */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Earnings Today</h2>
              <div className="space-y-2">
                <div className="text-sm">
                  <div className="font-medium">AAPL - Apple Inc.</div>
                  <div className="text-gray-500">After Close • Est. EPS: $1.95</div>
                </div>
                <div className="text-sm">
                  <div className="font-medium">MSFT - Microsoft</div>
                  <div className="text-gray-500">After Close • Est. EPS: $2.65</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}