import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import MarketIndices from '@/components/dashboard/MarketIndices'
import CryptoTracker from '@/components/dashboard/CryptoTracker'
import NewsFeed from '@/components/dashboard/NewsFeed'
import SentimentOverview from '@/components/dashboard/SentimentOverview'
import IPOTracker from '@/components/dashboard/IPOTracker'
import EarningsCalendar from '@/components/dashboard/EarningsCalendar'
import WatchlistManager from '@/components/dashboard/WatchlistManager'
import TechnicalAnalysis from '@/components/dashboard/TechnicalAnalysis'
import StockSentimentGrid from '@/components/dashboard/StockSentimentGrid'

export default async function DashboardPage() {
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Trading Dashboard</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Market Data */}
          <div className="lg:col-span-2 space-y-6">
            {/* Market Indices */}
            <MarketIndices />

            {/* Watchlist Manager */}
            <WatchlistManager />

            {/* Crypto Tracker */}
            <CryptoTracker />
            
            {/* Earnings Calendar */}
            <EarningsCalendar />
            
            {/* Technical Analysis */}
            <TechnicalAnalysis />
            
            {/* Stock Sentiment Grid */}
            <StockSentimentGrid />
          </div>

          {/* Right Column - News & Sentiment */}
          <div className="space-y-6">
            <NewsFeed />
            
            <SentimentOverview />
            
            <IPOTracker />
          </div>
        </div>
      </div>
    </div>
  )
}