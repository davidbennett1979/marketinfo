'use client'

import { useState, useEffect } from 'react'
import { PlusIcon, XIcon, TrendingUpIcon, TrendingDownIcon, SearchIcon, StarIcon, RefreshCwIcon } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { useRealTimeData } from '@/hooks/useRealTimeData'
import RealTimeStatus from '@/components/common/RealTimeStatus'
import { authenticatedFetch } from '@/lib/auth'

interface WatchlistItem {
  id: string
  symbol: string
  symbol_type: 'stock' | 'crypto'
  name?: string
  current_price?: number
  change_24h?: number
  change_percentage_24h?: number
  volume?: number
  market_cap?: number
  added_at: string
}

interface WatchlistManagerProps {
  className?: string
}

export default function WatchlistManager({ className = '' }: WatchlistManagerProps) {
  const [showAddForm, setShowAddForm] = useState(false)
  const [newSymbol, setNewSymbol] = useState('')
  const [newSymbolType, setNewSymbolType] = useState<'stock' | 'crypto'>('stock')
  const [addingSymbol, setAddingSymbol] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const supabase = createClient()

  // Use real-time data hook for watchlist
  const { 
    data: watchlist, 
    loading, 
    isConnected, 
    lastUpdate, 
    refetch 
  } = useRealTimeData<WatchlistItem[]>({
    url: `${process.env.NEXT_PUBLIC_API_URL}/api/watchlist`,
    refreshInterval: 20000, // 20 seconds for watchlist updates
    onError: (err) => setError(err.message)
  })


  const addToWatchlist = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!newSymbol.trim()) return
    
    try {
      setAddingSymbol(true)
      
      const response = await authenticatedFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/watchlist`, {
        method: 'POST',
        body: JSON.stringify({
          symbol: newSymbol.toUpperCase(),
          symbol_type: newSymbolType
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to add symbol')
      }
      
      const result = await response.json()
      
      if (result.success) {
        // Refresh watchlist with real-time data
        await refetch()
        setNewSymbol('')
        setShowAddForm(false)
        setError(null)
      } else {
        setError(result.message)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to add symbol')
      console.error('Add symbol error:', err)
    } finally {
      setAddingSymbol(false)
    }
  }

  const removeFromWatchlist = async (symbol: string) => {
    try {
      const response = await authenticatedFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/watchlist/${symbol}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        throw new Error('Failed to remove symbol')
      }
      
      // Refresh watchlist to update state
      await refetch()
      
    } catch (err) {
      setError('Failed to remove symbol')
      console.error('Remove symbol error:', err)
      // Refresh watchlist on error to sync state
      await refetch()
    }
  }

  const formatPrice = (price?: number) => {
    if (!price) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: price >= 1 ? 2 : 8
    }).format(price)
  }

  const formatPercentage = (percentage?: number) => {
    if (percentage === undefined || percentage === null) return 'N/A'
    const sign = percentage >= 0 ? '+' : ''
    return `${sign}${percentage.toFixed(2)}%`
  }

  const getChangeColor = (change?: number) => {
    if (!change) return 'text-gray-500'
    return change >= 0 ? 'text-green-600' : 'text-red-600'
  }

  const getChangeIcon = (change?: number) => {
    if (!change) return null
    return change >= 0 ? 
      <TrendingUpIcon className="w-3 h-3" /> : 
      <TrendingDownIcon className="w-3 h-3" />
  }

  if (loading && (!watchlist || watchlist.length === 0)) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <StarIcon className="w-5 h-5 mr-2 text-yellow-500" />
          My Watchlist
        </h2>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <StarIcon className="w-5 h-5 mr-2 text-yellow-500" />
          <h2 className="text-xl font-semibold">My Watchlist</h2>
          {watchlist && (
            <span className="ml-2 text-sm text-gray-500">({watchlist.length})</span>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <RealTimeStatus 
            isConnected={isConnected}
            lastUpdate={lastUpdate}
            onRefresh={refetch}
            className="text-xs"
          />
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="Add symbol to watchlist"
          >
            <PlusIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
          <button 
            onClick={() => setError(null)}
            className="ml-2 text-red-500 hover:text-red-700"
          >
            ×
          </button>
        </div>
      )}

      {/* Add Symbol Form */}
      {showAddForm && (
        <form onSubmit={addToWatchlist} className="mb-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex flex-col space-y-3">
            <div className="flex space-x-2">
              <div className="flex-1">
                <input
                  type="text"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  placeholder="Enter symbol (e.g., AAPL, BTC)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  disabled={addingSymbol}
                />
              </div>
              <select
                value={newSymbolType}
                onChange={(e) => setNewSymbolType(e.target.value as 'stock' | 'crypto')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                disabled={addingSymbol}
              >
                <option value="stock">Stock</option>
                <option value="crypto">Crypto</option>
              </select>
            </div>
            <div className="flex space-x-2">
              <button
                type="submit"
                disabled={addingSymbol || !newSymbol.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
              >
                {addingSymbol ? 'Adding...' : 'Add to Watchlist'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false)
                  setNewSymbol('')
                  setError(null)
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Watchlist Items */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {watchlist && watchlist.length > 0 ? (
          watchlist.map((item) => (
            <div key={item.id} className="border-b last:border-0 pb-3 last:pb-0 hover:bg-gray-50 rounded p-2 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="text-sm font-medium text-gray-900">
                      {item.name || item.symbol}
                    </h3>
                    <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
                      {item.symbol}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      item.symbol_type === 'stock' 
                        ? 'bg-blue-100 text-blue-700' 
                        : 'bg-orange-100 text-orange-700'
                    }`}>
                      {item.symbol_type}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 text-xs">
                    <span className="font-medium text-gray-900">
                      {formatPrice(item.current_price)}
                    </span>
                    {item.change_percentage_24h !== undefined && (
                      <span className={`flex items-center ${getChangeColor(item.change_percentage_24h)}`}>
                        {getChangeIcon(item.change_percentage_24h)}
                        <span className="ml-1">
                          {formatPercentage(item.change_percentage_24h)}
                        </span>
                      </span>
                    )}
                    {item.volume && (
                      <span className="text-gray-500">
                        Vol: {new Intl.NumberFormat('en-US', { notation: 'compact' }).format(item.volume)}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => removeFromWatchlist(item.symbol)}
                  className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                  title="Remove from watchlist"
                >
                  <XIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8">
            <SearchIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-2">Your watchlist is empty</p>
            <p className="text-gray-400 text-sm">Add stocks or crypto symbols to track them here</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
            >
              Add First Symbol
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      {watchlist && watchlist.length > 0 && (
        <div className="mt-4 pt-3 border-t">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Synced across all devices</span>
            <span>Auto-updates every 20s</span>
          </div>
        </div>
      )}
    </div>
  )
}