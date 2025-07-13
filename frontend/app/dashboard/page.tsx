import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'

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
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Market Overview */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
            <p className="text-gray-600">Market indices will appear here</p>
          </div>

          {/* Watchlist */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Watchlist</h2>
            <p className="text-gray-600">Your watched stocks will appear here</p>
          </div>

          {/* Top Movers */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Top Movers</h2>
            <p className="text-gray-600">Top gaining/losing stocks will appear here</p>
          </div>

          {/* Crypto Tracker */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Cryptocurrency</h2>
            <p className="text-gray-600">Crypto prices will appear here</p>
          </div>

          {/* News Feed */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Financial News</h2>
            <p className="text-gray-600">Latest news will appear here</p>
          </div>

          {/* Earnings Calendar */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Earnings Today</h2>
            <p className="text-gray-600">Earnings reports will appear here</p>
          </div>
        </div>
      </div>
    </div>
  )
}