'use client'

import { useState, useEffect } from 'react'
import { TrendingUpIcon, TrendingDownIcon, MinusIcon, ActivityIcon, BarChartIcon } from 'lucide-react'
import { TechnicalTooltip } from '@/components/common/SmartTooltip'
import { authenticatedFetch } from '@/lib/auth'

interface TechnicalIndicator {
  symbol: string
  name: string
  rsi: number
  macd: {
    macd: number
    signal: number
    histogram: number
  }
  sma_20: number
  sma_50: number
  bollinger_bands: {
    upper: number
    middle: number
    lower: number
  }
  current_price: number
  signal: 'buy' | 'sell' | 'hold'
  strength: 'strong' | 'moderate' | 'weak'
  last_updated: string
}

interface TechnicalAnalysisProps {
  className?: string
}

export default function TechnicalAnalysis({ className = '' }: TechnicalAnalysisProps) {
  const [indicators, setIndicators] = useState<TechnicalIndicator[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSymbol, setSelectedSymbol] = useState<string>('AAPL')

  // Popular symbols for technical analysis
  const symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']

  useEffect(() => {
    fetchTechnicalAnalysis()
    // Refresh every 5 minutes
    const interval = setInterval(fetchTechnicalAnalysis, 300000)
    return () => clearInterval(interval)
  }, [])

  const fetchTechnicalAnalysis = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🔍 Fetching technical analysis...')
      
      const response = await authenticatedFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/technical-analysis`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch technical analysis')
      }
      
      const data = await response.json()
      console.log('📊 Technical analysis data:', data)
      
      setIndicators(data)
    } catch (err) {
      console.error('❌ Technical analysis fetch error:', err)
      setError('Failed to load technical analysis')
      // Do not use mock data; keep indicators empty on failure
      setIndicators([])
    } finally {
      setLoading(false)
    }
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price)
  }

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'buy': return 'text-green-600'
      case 'sell': return 'text-red-600'
      case 'hold': return 'text-yellow-600'
      default: return 'text-gray-500'
    }
  }

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'buy': return <TrendingUpIcon className="w-4 h-4" />
      case 'sell': return <TrendingDownIcon className="w-4 h-4" />
      case 'hold': return <MinusIcon className="w-4 h-4" />
      default: return null
    }
  }

  const getRSIColor = (rsi: number) => {
    if (rsi >= 70) return 'text-red-600' // Overbought
    if (rsi <= 30) return 'text-green-600' // Oversold
    return 'text-yellow-600' // Neutral
  }

  const getRSILabel = (rsi: number) => {
    if (rsi >= 70) return 'Overbought'
    if (rsi <= 30) return 'Oversold'
    return 'Neutral'
  }

  const selectedIndicator = indicators.find(ind => ind.symbol === selectedSymbol) || indicators[0]

  if (loading && indicators.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <BarChartIcon className="w-5 h-5 mr-2 text-blue-500" />
          Technical Analysis
        </h2>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  // No data state
  if (!loading && !error && indicators.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold mb-2 flex items-center">
          <BarChartIcon className="w-5 h-5 mr-2 text-blue-500" />
          Technical Analysis
        </h2>
        <p className="text-sm text-gray-600">No technical data available right now. Try again shortly.</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center">
          <BarChartIcon className="w-5 h-5 mr-2 text-blue-500" />
          Technical Analysis
        </h2>
        <select
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {symbols.map(symbol => (
            <option key={symbol} value={symbol}>{symbol}</option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {selectedIndicator && (
        <div className="space-y-4">
          {/* Stock Info */}
          <div className="border-b pb-3">
            <TechnicalTooltip
              symbol={selectedIndicator.symbol}
              rsi={selectedIndicator.rsi}
              macd={selectedIndicator.macd}
              trend={selectedIndicator.signal as 'bullish' | 'bearish' | 'neutral'}
              signal={`${selectedIndicator.signal} (${selectedIndicator.strength} strength)`}
            >
              <div className="flex items-center justify-between cursor-help">
                <div>
                  <h3 className="font-medium text-lg">{selectedIndicator.name}</h3>
                  <span className="text-sm text-gray-500">{selectedIndicator.symbol}</span>
                </div>
                <div className="text-right">
                  <div className="text-xl font-semibold">
                    {formatPrice(selectedIndicator.current_price)}
                  </div>
                  <div className={`flex items-center text-sm ${getSignalColor(selectedIndicator.signal)}`}>
                    {getSignalIcon(selectedIndicator.signal)}
                    <span className="ml-1 capitalize">
                      {selectedIndicator.signal} ({selectedIndicator.strength})
                    </span>
                  </div>
                </div>
              </div>
            </TechnicalTooltip>
          </div>

          {/* Technical Indicators Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* RSI */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">RSI (14)</span>
                <span className={`text-sm font-semibold ${getRSIColor(selectedIndicator.rsi)}`}>
                  {getRSILabel(selectedIndicator.rsi)}
                </span>
              </div>
              <div className="flex items-center">
                <div className="text-lg font-bold">{selectedIndicator.rsi.toFixed(1)}</div>
                <div className="ml-3 flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${getRSIColor(selectedIndicator.rsi).replace('text-', 'bg-')}`}
                      style={{ width: `${selectedIndicator.rsi}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* MACD */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">MACD</span>
                <span className={`text-sm font-semibold ${
                  selectedIndicator.macd.histogram > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {selectedIndicator.macd.histogram > 0 ? 'Bullish' : 'Bearish'}
                </span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">MACD:</span>
                  <span className="font-medium">{selectedIndicator.macd.macd.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Signal:</span>
                  <span className="font-medium">{selectedIndicator.macd.signal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Histogram:</span>
                  <span className={`font-medium ${
                    selectedIndicator.macd.histogram > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {selectedIndicator.macd.histogram.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Moving Averages */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Moving Averages</span>
                <span className={`text-sm font-semibold ${
                  selectedIndicator.sma_20 > selectedIndicator.sma_50 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {selectedIndicator.sma_20 > selectedIndicator.sma_50 ? 'Bullish' : 'Bearish'}
                </span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">SMA 20:</span>
                  <span className="font-medium">{formatPrice(selectedIndicator.sma_20)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">SMA 50:</span>
                  <span className="font-medium">{formatPrice(selectedIndicator.sma_50)}</span>
                </div>
              </div>
            </div>

            {/* Bollinger Bands */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Bollinger Bands</span>
                <span className={`text-sm font-semibold ${
                  selectedIndicator.current_price > selectedIndicator.bollinger_bands.upper ? 'text-red-600' :
                  selectedIndicator.current_price < selectedIndicator.bollinger_bands.lower ? 'text-green-600' :
                  'text-yellow-600'
                }`}>
                  {selectedIndicator.current_price > selectedIndicator.bollinger_bands.upper ? 'Overbought' :
                   selectedIndicator.current_price < selectedIndicator.bollinger_bands.lower ? 'Oversold' :
                   'Neutral'}
                </span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Upper:</span>
                  <span className="font-medium">{formatPrice(selectedIndicator.bollinger_bands.upper)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Middle:</span>
                  <span className="font-medium">{formatPrice(selectedIndicator.bollinger_bands.middle)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Lower:</span>
                  <span className="font-medium">{formatPrice(selectedIndicator.bollinger_bands.lower)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="bg-gray-50 rounded-lg p-4 mt-4">
            <h4 className="font-medium text-gray-900 mb-2">Analysis Summary</h4>
            <div className={`flex items-center ${getSignalColor(selectedIndicator.signal)}`}>
              <ActivityIcon className="w-5 h-5 mr-2" />
              <span className="font-medium">
                {selectedIndicator.signal.toUpperCase()} Signal - {selectedIndicator.strength} strength
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {selectedIndicator.signal === 'buy' && 'Technical indicators suggest a bullish outlook. Consider entering a long position.'}
              {selectedIndicator.signal === 'sell' && 'Technical indicators suggest a bearish outlook. Consider taking profits or entering a short position.'}
              {selectedIndicator.signal === 'hold' && 'Mixed signals from technical indicators. Consider holding current position and monitoring closely.'}
            </p>
            <div className="text-xs text-gray-500 mt-2">
              Last updated: {new Date(selectedIndicator.last_updated).toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {/* Symbol Overview */}
      <div className="mt-6 pt-4 border-t">
        <h4 className="font-medium text-gray-900 mb-3">Quick Overview</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {indicators.slice(0, 4).map((indicator) => (
            <div 
              key={indicator.symbol} 
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedSymbol === indicator.symbol 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedSymbol(indicator.symbol)}
            >
              <div className="text-sm font-medium">{indicator.symbol}</div>
              <div className={`flex items-center text-xs ${getSignalColor(indicator.signal)}`}>
                {getSignalIcon(indicator.signal)}
                <span className="ml-1 capitalize">{indicator.signal}</span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                RSI: {indicator.rsi.toFixed(0)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
