'use client'

import { useStockPrice } from '@/hooks/useMarketData'
import { ArrowUpIcon, ArrowDownIcon, TrendingUpIcon } from 'lucide-react'
import SentimentIndicator from './SentimentIndicator'

interface StockCardProps {
  symbol: string
}

export default function StockCard({ symbol }: StockCardProps) {
  const { data, error, isLoading } = useStockPrice(symbol)

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="h-20 bg-gray-100 rounded animate-pulse" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-sm text-red-500">Failed to load {symbol}</p>
      </div>
    )
  }

  const isPositive = data.change_percent >= 0

  return (
    <div className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-bold text-lg">{data.symbol}</h3>
          <p className="text-sm text-gray-500 line-clamp-1">{data.name}</p>
        </div>
        <TrendingUpIcon className="w-5 h-5 text-gray-400" />
      </div>
      
      <div className="mt-3">
        <div className="text-2xl font-bold">${data.current_price}</div>
        <div className={`flex items-center mt-1 text-sm ${
          isPositive ? 'text-green-600' : 'text-red-600'
        }`}>
          {isPositive ? (
            <ArrowUpIcon className="w-4 h-4 mr-1" />
          ) : (
            <ArrowDownIcon className="w-4 h-4 mr-1" />
          )}
          <span>${Math.abs(data.change).toFixed(2)}</span>
          <span className="ml-1">({Math.abs(data.change_percent).toFixed(2)}%)</span>
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t space-y-2">
        <SentimentIndicator symbol={data.symbol} />
        <div className="flex justify-between text-xs text-gray-500">
          <span>Vol: {(data.volume / 1000000).toFixed(1)}M</span>
          <span>Cap: ${(data.market_cap / 1000000000).toFixed(1)}B</span>
        </div>
      </div>
    </div>
  )
}