'use client'

import { useMarketIndices } from '@/hooks/useMarketData'
import { ArrowUpIcon, ArrowDownIcon } from 'lucide-react'

export default function MarketIndices() {
  const { indices, error, isLoading } = useMarketIndices()

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Market Indices</h2>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Market Indices</h2>
        <p className="text-red-500">Failed to load market data</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Market Indices</h2>
      <div className="space-y-3">
        {indices.map((index: any) => (
          <div key={index.symbol} className="flex items-center justify-between p-3 bg-gray-50 rounded">
            <div>
              <div className="font-medium">{index.name}</div>
              <div className="text-sm text-gray-500">{index.symbol}</div>
            </div>
            <div className="text-right">
              <div className="font-semibold">${index.current_price?.toLocaleString()}</div>
              <div className={`flex items-center justify-end text-sm ${
                index.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {index.change_percent >= 0 ? (
                  <ArrowUpIcon className="w-4 h-4 mr-1" />
                ) : (
                  <ArrowDownIcon className="w-4 h-4 mr-1" />
                )}
                {Math.abs(index.change_percent)}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}