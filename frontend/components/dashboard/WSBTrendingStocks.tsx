'use client'

import { TrendingUpIcon, TrendingDownIcon, MinusIcon, FlameIcon, MessageSquareIcon, ArrowUpIcon } from 'lucide-react'
import { useRealTimeData } from '@/hooks/useRealTimeData'
import { SentimentTooltip } from '@/components/common/SmartTooltip'
import RealTimeStatus from '@/components/common/RealTimeStatus'

interface TrendingStock {
  symbol: string
  mention_count: number
  sentiment_score: number
  classification: 'bullish' | 'bearish' | 'neutral'
  confidence: number
  bullish_mentions: number
  bearish_mentions: number
  neutral_mentions: number
  top_post?: {
    title: string
    upvotes: number
    url: string
  }
  rationale: string
  last_updated: string
}

interface WSBTrendingResponse {
  trending_stocks: TrendingStock[]
  total_posts_analyzed: number
  source: string
  last_updated: string
}

export default function WSBTrendingStocks() {
  const { 
    data, 
    loading, 
    error, 
    isConnected, 
    lastUpdate, 
    refetch 
  } = useRealTimeData<WSBTrendingResponse>({
    url: `${process.env.NEXT_PUBLIC_API_URL}/api/sentiment/stocks/wsb-trending?limit=5`,
    refreshInterval: 600000, // 10 minutes
    onData: (data) => {
      console.log('🔥 WSB trending stocks updated:', data.trending_stocks.length)
    }
  })

  const getSentimentIcon = (classification: string) => {
    switch (classification) {
      case 'bullish': return <TrendingUpIcon className="w-4 h-4" />
      case 'bearish': return <TrendingDownIcon className="w-4 h-4" />
      default: return <MinusIcon className="w-4 h-4" />
    }
  }

  const getSentimentColor = (classification: string) => {
    switch (classification) {
      case 'bullish': return 'text-green-600'
      case 'bearish': return 'text-red-600'
      default: return 'text-yellow-600'
    }
  }

  const getConfidenceWidth = (confidence: number) => {
    return `${Math.min(confidence * 100, 100)}%`
  }

  if (loading && !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <FlameIcon className="w-5 h-5 mr-2 text-orange-500" />
          WSB Trending Stocks
        </h2>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <FlameIcon className="w-5 h-5 mr-2 text-orange-500" />
          WSB Trending Stocks
        </h2>
        <p className="text-red-500 text-sm">Failed to load trending stocks</p>
      </div>
    )
  }

  const trendingStocks = data?.trending_stocks || []

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center">
          <FlameIcon className="w-5 h-5 mr-2 text-orange-500" />
          WSB Trending Stocks
        </h2>
        <RealTimeStatus 
          isConnected={isConnected}
          lastUpdate={lastUpdate}
          onRefresh={refetch}
          className="text-xs"
        />
      </div>

      <div className="text-xs text-gray-500 mb-4">
        Most talked about stocks on r/wallstreetbets
      </div>

      <div className="space-y-3">
        {trendingStocks.map((stock, index) => (
          <div 
            key={stock.symbol}
            className="border rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-8 h-8 bg-orange-100 rounded-full text-orange-600 font-bold text-sm">
                  {index + 1}
                </div>
                <div>
                  <SentimentTooltip
                    symbol={stock.symbol}
                    sentiment={stock.classification}
                    score={stock.sentiment_score}
                    confidence={stock.confidence}
                    rationale={stock.rationale}
                    postCount={stock.mention_count}
                    source="r/wallstreetbets"
                  >
                    <h3 className="font-bold text-lg cursor-help">{stock.symbol}</h3>
                  </SentimentTooltip>
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <MessageSquareIcon className="w-3 h-3" />
                    <span>{stock.mention_count} mentions</span>
                  </div>
                </div>
              </div>
              
              <div className={`flex items-center ${getSentimentColor(stock.classification)}`}>
                {getSentimentIcon(stock.classification)}
                <span className="ml-1 font-medium capitalize">
                  {stock.classification}
                </span>
              </div>
            </div>

            {/* Sentiment Breakdown */}
            <div className="mb-3">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Sentiment Score</span>
                <span className="font-medium">
                  {(stock.sentiment_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    stock.classification === 'bullish' ? 'bg-green-500' :
                    stock.classification === 'bearish' ? 'bg-red-500' :
                    'bg-yellow-500'
                  }`}
                  style={{ width: getConfidenceWidth(stock.confidence) }}
                />
              </div>
            </div>

            {/* Mention Breakdown */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-4">
                <span className="text-green-600">
                  ↑ {stock.bullish_mentions}
                </span>
                <span className="text-red-600">
                  ↓ {stock.bearish_mentions}
                </span>
                <span className="text-gray-500">
                  — {stock.neutral_mentions}
                </span>
              </div>
            </div>

            {/* Top Post */}
            {stock.top_post && (
              <div className="mt-3 pt-3 border-t">
                <div className="text-xs text-gray-500 mb-1">Top Post:</div>
                <a 
                  href={stock.top_post.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-700 line-clamp-1"
                >
                  {stock.top_post.title}
                </a>
                <div className="flex items-center text-xs text-gray-500 mt-1">
                  <ArrowUpIcon className="w-3 h-3 mr-1" />
                  {stock.top_post.upvotes.toLocaleString()} upvotes
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {data && (
        <div className="mt-4 pt-3 border-t text-xs text-gray-500 text-center">
          Analyzed {data.total_posts_analyzed} posts from {data.source}
        </div>
      )}
    </div>
  )
}