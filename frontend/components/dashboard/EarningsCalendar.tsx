'use client'

import { useState, useEffect } from 'react'
import { CalendarIcon, ClockIcon, TrendingUpIcon, InfoIcon, RefreshCwIcon } from 'lucide-react'
import SmartTooltip, { EarningsTooltip } from '@/components/common/SmartTooltip'
import { authenticatedFetch } from '@/lib/auth'

interface Earning {
  company: string
  symbol: string
  date: string
  time: string
  eps_estimate: string
  source: string
}

interface EarningsCalendarProps {
  className?: string
}

interface TooltipProps {
  children: React.ReactNode
  content: string
  className?: string
}

// const Tooltip = ({ children, content, className = '' }: TooltipProps) => (
//   <div className={`relative ${className}`} title={content}>
//     {children}
//   </div>
// )

export default function EarningsCalendar({ className = '' }: EarningsCalendarProps) {
  const [upcomingEarnings, setUpcomingEarnings] = useState<Earning[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    fetchEarningsData()
  }, [])

  const fetchEarningsData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await authenticatedFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/earnings/upcoming?days_ahead=5`)
      if (!response.ok) throw new Error('Failed to fetch earnings data')
      
      const data = await response.json()
      setUpcomingEarnings(data)
    } catch (err) {
      setError('Failed to load earnings data')
      console.error('Earnings fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      if (isNaN(date.getTime())) return dateStr
      
      const today = new Date()
      const tomorrow = new Date(today)
      tomorrow.setDate(tomorrow.getDate() + 1)
      
      if (date.toDateString() === today.toDateString()) {
        return 'Today'
      } else if (date.toDateString() === tomorrow.toDateString()) {
        return 'Tomorrow'
      } else {
        return date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric',
          weekday: 'short'
        })
      }
    } catch {
      return dateStr
    }
  }

  const getTimeColor = (time: string) => {
    if (time.toLowerCase().includes('before')) {
      return 'text-blue-600 bg-blue-50'
    } else if (time.toLowerCase().includes('after')) {
      return 'text-purple-600 bg-purple-50'
    } else {
      return 'text-gray-600 bg-gray-50'
    }
  }

  const getTimeIcon = () => {
    return <ClockIcon className="w-3 h-3" />
  }

  // const getCompanyTooltip = (earning: Earning) => {
  //   return `${earning.company} reports earnings ${earning.time.toLowerCase()}. EPS estimate: ${earning.eps_estimate}`
  // }

  const getTimeTooltip = (timeStr: string) => {
    const time = timeStr;
    if (time.toLowerCase().includes('before')) {
      return 'Earnings announced before market opens (pre-market)'
    } else if (time.toLowerCase().includes('after')) {
      return 'Earnings announced after market closes (after-hours)'
    } else {
      return 'Earnings timing to be determined'
    }
  }

  const getEPSTooltip = () => {
    return `Expected earnings per share. Actual results may vary and can significantly impact stock price.`
  }

  // Group earnings by date (keeping for future use)
  // const groupedEarnings = upcomingEarnings.reduce((groups, earning) => {
  //   const date = earning.date
  //   if (!groups[date]) {
  //     groups[date] = []
  //   }
  //   groups[date].push(earning)
  //   return groups
  // }, {} as Record<string, Earning[]>)

  const displayedEarnings = showAll ? upcomingEarnings : upcomingEarnings.slice(0, 6)

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <TrendingUpIcon className="w-5 h-5 mr-2 text-green-500" />
          Earnings Calendar
        </h2>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
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
          <TrendingUpIcon className="w-5 h-5 mr-2 text-green-500" />
          Earnings Calendar
        </h2>
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center">
          <TrendingUpIcon className="w-5 h-5 mr-2 text-green-500" />
          Earnings Calendar
        </h2>
        <div className="flex items-center space-x-2">
          <SmartTooltip 
            content="View upcoming quarterly earnings announcements from major companies. Earnings reports can significantly impact stock prices."
            type="earnings"
          >
            <InfoIcon className="w-4 h-4 text-gray-400 hover:text-gray-600" />
          </SmartTooltip>
          <button
            onClick={fetchEarningsData}
            className="p-1 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
            title="Refresh earnings data"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Earnings List */}
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {displayedEarnings.length > 0 ? (
          displayedEarnings.map((earning, index) => (
            <div key={index} className="border-b last:border-0 pb-3 last:pb-0 hover:bg-gray-50 rounded p-2 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <EarningsTooltip
                      symbol={earning.symbol}
                      date={earning.date}
                      time={earning.time.includes('Before') ? 'pre-market' : 'after-market'}
                      estimate={earning.eps_estimate !== 'N/A' ? parseFloat(earning.eps_estimate.replace('$', '')) : undefined}
                    >
                      <h3 className="text-sm font-medium text-gray-900 cursor-help">
                        {earning.company}
                      </h3>
                    </EarningsTooltip>
                    <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
                      {earning.symbol}
                    </span>
                    {earning.source === 'Mock Data' && (
                      <span className="text-xs bg-amber-100 text-amber-700 px-1 py-0.5 rounded">
                        Demo
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span className="flex items-center">
                      <CalendarIcon className="w-3 h-3 mr-1" />
                      {formatDate(earning.date)}
                    </span>
                    <SmartTooltip content={getTimeTooltip(earning.time)} type="earnings">
                      <span className={`flex items-center px-2 py-0.5 rounded-full text-xs font-medium cursor-help ${getTimeColor(earning.time)}`}>
                        {getTimeIcon()}
                        <span className="ml-1">
                          {earning.time.includes('Before') ? 'Pre-Market' : 
                           earning.time.includes('After') ? 'After-Hours' : 'TBD'}
                        </span>
                      </span>
                    </SmartTooltip>
                    {earning.eps_estimate && earning.eps_estimate !== 'N/A' && (
                      <SmartTooltip content={getEPSTooltip()} type="earnings">
                        <span className="cursor-help font-medium">
                          EPS: {earning.eps_estimate}
                        </span>
                      </SmartTooltip>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-500 text-sm text-center py-4">
            No upcoming earnings found
          </p>
        )}
      </div>

      {/* Show More/Less Button */}
      {upcomingEarnings.length > 6 && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {showAll ? 'Show Less' : `Show All (${upcomingEarnings.length})`}
          </button>
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 pt-3 border-t">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <SmartTooltip content="Earnings data aggregated from Yahoo Finance and MarketWatch calendars for comprehensive coverage" type="earnings">
            <span className="cursor-help">Data from multiple sources</span>
          </SmartTooltip>
          <SmartTooltip content="Earnings dates and estimates may change. Always verify with company announcements before trading." type="earnings">
            <span className="cursor-help">Updated every 2 hours</span>
          </SmartTooltip>
        </div>
        
        <div className="flex items-center justify-center space-x-6 mt-2 text-xs">
          <div className="flex items-center">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-1" />
            <span>Pre-Market</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-purple-500 rounded-full mr-1" />
            <span>After-Hours</span>
          </div>
        </div>
      </div>
    </div>
  )
}