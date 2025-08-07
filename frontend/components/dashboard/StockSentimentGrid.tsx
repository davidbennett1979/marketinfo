'use client'

import { useState } from 'react'
import { TrendingUpIcon, TrendingDownIcon, MinusIcon, MessageSquareIcon, InfoIcon } from 'lucide-react'
import { useRealTimeData } from '@/hooks/useRealTimeData'
import RealTimeStatus from '@/components/common/RealTimeStatus'

interface StockSentiment {
  symbol: string
  sentiment_score: number
  classification: 'bullish' | 'bearish' | 'neutral'
  confidence: number
  post_count: number
  bullish_mentions: number
  bearish_mentions: number
  rationale: string
  last_updated: string
}

interface StockSentimentGridProps {
  className?: string
  limit?: number
}

export default function StockSentimentGrid({ className = '', limit = 15 }: StockSentimentGridProps) {
  const [selectedStock, setSelectedStock] = useState<string | null>(null)

  // Use real-time data hook for expanded sentiment
  const { 
    data: sentimentData, 
    loading, 
    error,
    isConnected, 
    lastUpdate, 
    refetch 
  } = useRealTimeData<{stocks: StockSentiment[], total_count: number, source: string}>({
    url: `${process.env.NEXT_PUBLIC_API_URL}/api/sentiment/stocks/popular?limit=${limit}`,
    refreshInterval: 180000, // 3 minutes for sentiment updates
    onError: (err) => console.error('❌ Stock sentiment error:', err.message)
  })

  const getSentimentColor = (classification: string) => {
    switch (classification) {
      case 'bullish': return 'text-green-600'
      case 'bearish': return 'text-red-600'
      case 'neutral': return 'text-yellow-600'
      default: return 'text-gray-600'
    }
  }

  const getSentimentBgColor = (classification: string, isSelected: boolean = false) => {
    if (isSelected) {
      switch (classification) {
        case 'bullish': return 'bg-green-100 border-green-300'
        case 'bearish': return 'bg-red-100 border-red-300'
        case 'neutral': return 'bg-yellow-100 border-yellow-300'
        default: return 'bg-gray-100 border-gray-300'
      }
    }
    
    switch (classification) {
      case 'bullish': return 'bg-green-50 border-green-200 hover:bg-green-100'
      case 'bearish': return 'bg-red-50 border-red-200 hover:bg-red-100'
      case 'neutral': return 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100'
      default: return 'bg-gray-50 border-gray-200 hover:bg-gray-100'
    }
  }

  const getSentimentIcon = (classification: string) => {
    switch (classification) {
      case 'bullish': return <TrendingUpIcon className="w-4 h-4" />
      case 'bearish': return <TrendingDownIcon className="w-4 h-4" />
      case 'neutral': return <MinusIcon className="w-4 h-4" />
      default: return null
    }
  }

  const formatSentimentScore = (score: number) => {
    const percentage = (score * 100).toFixed(0)
    const sign = score >= 0 ? '+' : ''
    return `${sign}${percentage}%`
  }

  const getConfidenceWidth = (confidence: number) => {
    return `${Math.min(confidence * 100, 100)}%`
  }

  if (loading && (!sentimentData?.stocks || sentimentData.stocks.length === 0)) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <MessageSquareIcon className="w-5 h-5 mr-2 text-purple-500" />
          Stock Sentiment Analysis
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {Array.from({ length: 15 }, (_, i) => (
            <div key={i} className="h-20 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  const stocks = sentimentData?.stocks || []

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <MessageSquareIcon className="w-5 h-5 mr-2 text-purple-500" />
          <h2 className="text-xl font-semibold">Stock Sentiment Analysis</h2>
          {sentimentData?.total_count && (
            <span className="ml-2 text-sm text-gray-500">
              ({sentimentData.total_count} stocks)
            </span>
          )}
        </div>
        <RealTimeStatus 
          isConnected={isConnected}
          lastUpdate={lastUpdate}
          onRefresh={refetch}
          className="text-xs"
        />
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          Failed to load sentiment data
        </div>
      )}

      {/* Sentiment Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
        {stocks.map((stock) => (
          <div
            key={stock.symbol}
            className={`p-3 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
              getSentimentBgColor(stock.classification, selectedStock === stock.symbol)
            }`}
            onClick={() => setSelectedStock(selectedStock === stock.symbol ? null : stock.symbol)}
            title={stock.rationale}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-sm">{stock.symbol}</span>
              <div className={`flex items-center ${getSentimentColor(stock.classification)}`}>
                {getSentimentIcon(stock.classification)}
              </div>
            </div>
            
            <div className="space-y-1">
              <div className={`text-xs font-medium ${getSentimentColor(stock.classification)}`}>
                {formatSentimentScore(stock.sentiment_score)}
              </div>
              
              {/* Confidence Bar */}
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full ${getSentimentColor(stock.classification).replace('text-', 'bg-')}`}
                  style={{ width: getConfidenceWidth(stock.confidence) }}
                />
              </div>
              
              <div className="flex justify-between text-xs text-gray-500">
                <span>{stock.post_count} posts</span>
                <span className="capitalize text-xs">{stock.classification}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detailed View */}
      {selectedStock && (
        <div className="border-t pt-4">
          {(() => {
            const stock = stocks.find(s => s.symbol === selectedStock)
            if (!stock) return null

            return (
              <div className={`p-4 rounded-lg ${getSentimentBgColor(stock.classification, true)}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    <h3 className="text-lg font-semibold mr-2">{stock.symbol}</h3>
                    <div className={`flex items-center ${getSentimentColor(stock.classification)}`}>
                      {getSentimentIcon(stock.classification)}
                      <span className="ml-1 text-sm font-medium capitalize">
                        {stock.classification} ({formatSentimentScore(stock.sentiment_score)})
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedStock(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-xs text-gray-500">Total Posts</div>
                    <div className="text-lg font-semibold">{stock.post_count}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-gray-500">Bullish Mentions</div>
                    <div className="text-lg font-semibold text-green-600">{stock.bullish_mentions}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-gray-500">Bearish Mentions</div>
                    <div className="text-lg font-semibold text-red-600">{stock.bearish_mentions}</div>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="flex items-center mb-2">
                    <InfoIcon className="w-4 h-4 mr-2 text-blue-500" />
                    <span className="font-medium text-sm">Analysis Rationale</span>
                  </div>
                  <p className="text-sm text-gray-700 bg-white/50 p-3 rounded">
                    {stock.rationale}
                  </p>
                </div>

                <div className="text-xs text-gray-500">
                  Last updated: {new Date(stock.last_updated).toLocaleString()}
                </div>
              </div>
            )
          })()}
        </div>
      )}

      {/* Summary Stats */}
      {stocks.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-gray-500">Bullish Stocks</div>
              <div className="text-lg font-semibold text-green-600">
                {stocks.filter(s => s.classification === 'bullish').length}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Bearish Stocks</div>
              <div className="text-lg font-semibold text-red-600">
                {stocks.filter(s => s.classification === 'bearish').length}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Neutral Stocks</div>
              <div className="text-lg font-semibold text-yellow-600">
                {stocks.filter(s => s.classification === 'neutral').length}
              </div>
            </div>
          </div>
          
          <div className="mt-3 text-center">
            <div className="text-xs text-gray-500">
              Data from {sentimentData?.source || 'r/wallstreetbets'} • Updates every 3 minutes
            </div>
          </div>
        </div>
      )}
    </div>
  )
}