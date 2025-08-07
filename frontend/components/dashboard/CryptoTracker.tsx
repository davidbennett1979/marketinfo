'use client'

import { ArrowUpIcon, ArrowDownIcon, DollarSignIcon } from 'lucide-react'
import { useCryptoData } from '@/hooks/useRealTimeData'
import RealTimeStatus from '@/components/common/RealTimeStatus'

export default function CryptoTracker() {
  const { 
    data: cryptos, 
    loading: isLoading, 
    error, 
    isConnected, 
    lastUpdate, 
    refetch 
  } = useCryptoData()

  if (isLoading && (!cryptos || cryptos.length === 0)) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Top Cryptocurrencies</h2>
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Top Cryptocurrencies</h2>
        <p className="text-red-500">Failed to load crypto data</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center">
          <DollarSignIcon className="w-5 h-5 mr-2 text-orange-500" />
          Top Cryptocurrencies
        </h2>
        <RealTimeStatus 
          isConnected={isConnected}
          lastUpdate={lastUpdate}
          onRefresh={refetch}
          className="text-xs"
        />
      </div>
      <div className="space-y-2">
        {cryptos && cryptos.map((crypto: any) => (
          <div key={crypto.symbol} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
            <div className="flex items-center">
              <div className="mr-3">
                <div className="font-medium">{crypto.symbol}</div>
                <div className="text-xs text-gray-500">{crypto.name}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="font-medium">${crypto.current_price?.toLocaleString()}</div>
              <div className={`flex items-center justify-end text-sm ${
                crypto.change_percent_24h >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {crypto.change_percent_24h >= 0 ? (
                  <ArrowUpIcon className="w-3 h-3 mr-1" />
                ) : (
                  <ArrowDownIcon className="w-3 h-3 mr-1" />
                )}
                {Math.abs(crypto.change_percent_24h).toFixed(2)}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}