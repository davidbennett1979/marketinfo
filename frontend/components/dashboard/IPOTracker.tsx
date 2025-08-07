'use client'

import { useState, useEffect } from 'react'
import { CalendarIcon, TrendingUpIcon, TrendingDownIcon, BuildingIcon, DollarSignIcon, InfoIcon } from 'lucide-react'

interface IPO {
  company: string
  symbol: string
  date: string
  price_range: string
  shares: string
  market_cap: string
  source: string
}

interface RecentIPO {
  company: string
  symbol: string
  ipo_date: string
  ipo_price: number
  current_price: number
  change_percent: number
  first_day_close: number
  market_cap: string
  performance: string
}

interface IPOTrackerProps {
  className?: string
}

interface TooltipProps {
  children: React.ReactNode
  content: string
  className?: string
}

const Tooltip = ({ children, content, className = '' }: TooltipProps) => (
  <div className={`relative ${className}`} title={content}>
    {children}
  </div>
)

export default function IPOTracker({ className = '' }: IPOTrackerProps) {
  const [upcomingIPOs, setUpcomingIPOs] = useState<IPO[]>([])
  const [recentIPOs, setRecentIPOs] = useState<RecentIPO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'upcoming' | 'recent'>('upcoming')

  useEffect(() => {
    fetchIPOData()
  }, [])

  const fetchIPOData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🧪 Fetching IPO data from:', `${process.env.NEXT_PUBLIC_API_URL}/api/ipo/upcoming`)
      
      const [upcomingResponse, recentResponse] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ipo/upcoming?days_ahead=30`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ipo/recent?days_back=30`)
      ])
      
      console.log('📊 Response status:', upcomingResponse.status, recentResponse.status)
      
      if (!upcomingResponse.ok || !recentResponse.ok) {
        throw new Error('Failed to fetch IPO data')
      }
      
      const upcomingData = await upcomingResponse.json()
      const recentData = await recentResponse.json()
      
      console.log('✅ Upcoming IPOs:', upcomingData)
      console.log('✅ Recent IPOs:', recentData)
      
      setUpcomingIPOs(upcomingData.slice(0, 8)) // Show top 8
      setRecentIPOs(recentData.slice(0, 6))
    } catch (err) {
      setError('Failed to load IPO data')
      console.error('❌ IPO fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      if (isNaN(date.getTime())) return dateStr
      
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  const getDaysUntilIPO = (dateStr: string): string => {
    try {
      const ipoDate = new Date(dateStr)
      const today = new Date()
      const diffTime = ipoDate.getTime() - today.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      
      if (diffDays < 0) return 'Past'
      if (diffDays === 0) return 'Today'
      if (diffDays === 1) return 'Tomorrow'
      return `${diffDays} days`
    } catch {
      return 'TBD'
    }
  }

  const getPerformanceColor = (changePercent: number) => {
    if (changePercent > 0) return 'text-green-600'
    if (changePercent < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const getPerformanceIcon = (changePercent: number) => {
    if (changePercent > 0) return <TrendingUpIcon className="w-3 h-3" />
    if (changePercent < 0) return <TrendingDownIcon className="w-3 h-3" />
    return null
  }

  const getPriceRangeTooltip = (_priceRange: string) => {
    return `Expected IPO price range. Final price may differ based on market demand and investor interest.`
  }

  const getCompanyTooltip = (company: string, symbol: string) => {
    return `${company} (${symbol}) - Click to research this company before investing.`
  }

  const getDateTooltip = (date: string) => {
    const daysUntil = getDaysUntilIPO(date)
    return `IPO expected ${formatDate(date)} (${daysUntil}). Date may change based on market conditions.`
  }

  const getPerformanceTooltip = (ipo: RecentIPO) => {
    const dayOneGain = ((ipo.first_day_close - ipo.ipo_price) / ipo.ipo_price * 100).toFixed(1)
    return `First day: +${dayOneGain}% | Current: ${ipo.change_percent > 0 ? '+' : ''}${ipo.change_percent.toFixed(1)}% from IPO price`
  }

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <CalendarIcon className="w-5 h-5 mr-2 text-blue-500" />
          IPO Tracker
        </h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <CalendarIcon className="w-5 h-5 mr-2 text-blue-500" />
          IPO Tracker
        </h2>
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center">
          <CalendarIcon className="w-5 h-5 mr-2 text-blue-500" />
          IPO Tracker
        </h2>
        <Tooltip content="Initial Public Offerings - Companies going public on stock exchanges">
          <InfoIcon className="w-4 h-4 text-gray-400 hover:text-gray-600" />
        </Tooltip>
      </div>
      
      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-4 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('upcoming')}
          className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'upcoming'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          <Tooltip content="Companies planning to go public soon">
            <span>Upcoming ({upcomingIPOs.length})</span>
          </Tooltip>
        </button>
        <button
          onClick={() => setActiveTab('recent')}
          className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'recent'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          <Tooltip content="Recently public companies and their performance">
            <span>Recent ({recentIPOs.length})</span>
          </Tooltip>
        </button>
      </div>

      {/* Content */}
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {activeTab === 'upcoming' ? (
          upcomingIPOs.length > 0 ? (
            upcomingIPOs.map((ipo, index) => (
              <div key={index} className="border-b last:border-0 pb-3 last:pb-0 hover:bg-gray-50 rounded p-2 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <BuildingIcon className="w-4 h-4 text-gray-400" />
                      <Tooltip content={getCompanyTooltip(ipo.company, ipo.symbol)}>
                        <h3 className="text-sm font-medium text-gray-900 cursor-help">
                          {ipo.company}
                        </h3>
                      </Tooltip>
                      {ipo.symbol !== 'TBD' && (
                        <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
                          {ipo.symbol}
                        </span>
                      )}
                      {ipo.source === 'Mock Data' && (
                        <span className="text-xs bg-amber-100 text-amber-700 px-1 py-0.5 rounded">
                          Demo
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <Tooltip content={getDateTooltip(ipo.date)}>
                        <span className="flex items-center cursor-help">
                          <CalendarIcon className="w-3 h-3 mr-1" />
                          {formatDate(ipo.date)} ({getDaysUntilIPO(ipo.date)})
                        </span>
                      </Tooltip>
                      <Tooltip content={getPriceRangeTooltip(ipo.price_range)}>
                        <span className="flex items-center cursor-help">
                          <DollarSignIcon className="w-3 h-3 mr-1" />
                          {ipo.price_range}
                        </span>
                      </Tooltip>
                      {ipo.shares !== 'N/A' && (
                        <Tooltip content="Number of shares being offered to the public">
                          <span className="cursor-help">{ipo.shares} shares</span>
                        </Tooltip>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-400">{ipo.source}</div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-sm text-center py-4">
              No upcoming IPOs found
            </p>
          )
        ) : (
          recentIPOs.length > 0 ? (
            recentIPOs.map((ipo, index) => (
              <div key={index} className="border-b last:border-0 pb-3 last:pb-0 hover:bg-gray-50 rounded p-2 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <BuildingIcon className="w-4 h-4 text-gray-400" />
                      <h3 className="text-sm font-medium text-gray-900">
                        {ipo.company}
                      </h3>
                      <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
                        {ipo.symbol}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>IPO: ${ipo.ipo_price.toFixed(2)}</span>
                      <span>Current: ${ipo.current_price.toFixed(2)}</span>
                      <span>{formatDate(ipo.ipo_date)}</span>
                    </div>
                  </div>
                  <Tooltip content={getPerformanceTooltip(ipo)}>
                    <div className={`flex items-center text-xs font-medium cursor-help ${getPerformanceColor(ipo.change_percent)}`}>
                      {getPerformanceIcon(ipo.change_percent)}
                      <span className="ml-1">
                        {ipo.change_percent > 0 ? '+' : ''}{ipo.change_percent.toFixed(1)}%
                      </span>
                    </div>
                  </Tooltip>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-sm text-center py-4">
              No recent IPOs found
            </p>
          )
        )}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <Tooltip content="Data sourced from MarketWatch and Yahoo Finance IPO calendars">
            <span className="cursor-help">IPO data from multiple sources</span>
          </Tooltip>
          <Tooltip content="IPO dates and details may change. Always verify before investing.">
            <span className="cursor-help">Updated every 4 hours</span>
          </Tooltip>
        </div>
      </div>
    </div>
  )
}