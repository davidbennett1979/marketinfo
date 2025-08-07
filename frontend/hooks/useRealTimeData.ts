'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

interface RealTimeConfig {
  url: string
  refreshInterval?: number  // in milliseconds
  maxRetries?: number
  retryDelay?: number
  onData?: (data: any) => void
  onError?: (error: Error) => void
}

interface RealTimeState<T> {
  data: T | null
  loading: boolean
  error: string | null
  isConnected: boolean
  lastUpdate: Date | null
}

export function useRealTimeData<T>(config: RealTimeConfig): RealTimeState<T> & {
  refetch: () => Promise<void>
  connect: () => void
  disconnect: () => void
} {
  const [state, setState] = useState<RealTimeState<T>>({
    data: null,
    loading: true,
    error: null,
    isConnected: false,
    lastUpdate: null
  })
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const retryCountRef = useRef(0)
  const isActiveRef = useRef(true)
  
  const {
    url,
    refreshInterval = 300000, // 5 minutes default (much slower)
    maxRetries = 5,
    retryDelay = 2000,
    onData,
    onError
  } = config

  // Store callbacks in refs to avoid dependency issues
  const onDataRef = useRef(onData)
  const onErrorRef = useRef(onError)
  
  useEffect(() => {
    onDataRef.current = onData
    onErrorRef.current = onError
  }, [onData, onError])

  const fetchData = useCallback(async (): Promise<void> => {
    if (!isActiveRef.current) return

    try {
      setState(prev => ({ ...prev, loading: prev.data === null }))
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      if (!isActiveRef.current) return
      
      setState(prev => ({
        ...prev,
        data,
        loading: false,
        error: null,
        isConnected: true,
        lastUpdate: new Date()
      }))
      
      retryCountRef.current = 0
      onDataRef.current?.(data)
      
    } catch (error) {
      if (!isActiveRef.current) return
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      console.error(`Real-time data fetch error for ${url}:`, errorMessage)
      
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
        isConnected: false
      }))
      
      onErrorRef.current?.(error instanceof Error ? error : new Error(errorMessage))
      
      // Retry logic
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current++
        setTimeout(() => {
          if (isActiveRef.current) {
            fetchData()
          }
        }, retryDelay * retryCountRef.current)
      }
    }
  }, [url, maxRetries, retryDelay])

  const connect = useCallback(() => {
    if (intervalRef.current) return
    
    isActiveRef.current = true
    setState(prev => ({ ...prev, isConnected: true }))
    
    // Initial fetch
    fetchData()
    
    // Set up polling
    intervalRef.current = setInterval(fetchData, refreshInterval)
  }, [fetchData, refreshInterval])

  const disconnect = useCallback(() => {
    isActiveRef.current = false
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    
    setState(prev => ({ ...prev, isConnected: false }))
  }, [])

  const refetch = useCallback(async (): Promise<void> => {
    await fetchData()
  }, [fetchData])

  // Store connect/disconnect in refs to avoid stale closures
  const connectRef = useRef(connect)
  const disconnectRef = useRef(disconnect)
  
  useEffect(() => {
    connectRef.current = connect
    disconnectRef.current = disconnect
  }, [connect, disconnect])

  // Auto-connect on mount
  useEffect(() => {
    connectRef.current()
    
    // Handle page visibility changes
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        connectRef.current()
      } else {
        disconnectRef.current()
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    // Cleanup
    return () => {
      disconnectRef.current()
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, []) // Now safe to have empty deps

  return {
    ...state,
    refetch,
    connect,
    disconnect
  }
}

// Specialized hook for market data
export function useMarketData(symbols: string[] = []) {
  const url = `${process.env.NEXT_PUBLIC_API_URL}/api/stocks/prices?symbols=${symbols.join(',')}`
  
  return useRealTimeData<Record<string, any>>({
    url,
    refreshInterval: 120000, // 2 minutes for market data
    onData: (data) => {
      console.log('📊 Market data updated:', Object.keys(data).length, 'symbols')
    },
    onError: (error) => {
      console.error('❌ Market data error:', error.message)
    }
  })
}

// Specialized hook for sentiment data
export function useSentimentData() {
  return useRealTimeData<any[]>({
    url: `${process.env.NEXT_PUBLIC_API_URL}/api/sentiment`,
    refreshInterval: 300000, // 5 minutes for sentiment
    onData: (data) => {
      console.log('💭 Sentiment data updated:', data.length, 'entries')
    },
    onError: (error) => {
      console.error('❌ Sentiment data error:', error.message)
    }
  })
}

// Specialized hook for crypto data
export function useCryptoData() {
  return useRealTimeData<any[]>({
    url: `${process.env.NEXT_PUBLIC_API_URL}/api/crypto`,
    refreshInterval: 180000, // 3 minutes for crypto
    onData: (data) => {
      console.log('₿ Crypto data updated:', data.length, 'currencies')
    },
    onError: (error) => {
      console.error('❌ Crypto data error:', error.message)
    }
  })
}

// Hook for news updates
export function useNewsData() {
  return useRealTimeData<any[]>({
    url: `${process.env.NEXT_PUBLIC_API_URL}/api/news`,
    refreshInterval: 600000, // 10 minutes for news
    onData: (data) => {
      console.log('📰 News data updated:', data.length, 'articles')
    },
    onError: (error) => {
      console.error('❌ News data error:', error.message)
    }
  })
}