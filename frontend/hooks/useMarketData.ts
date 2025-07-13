import useSWR from 'swr'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to fetch')
  return res.json()
}

export function useStockPrice(symbol: string) {
  const { data, error, isLoading } = useSWR(
    symbol ? `${API_BASE_URL}/api/stocks/price/${symbol}` : null,
    fetcher,
    {
      refreshInterval: 60000, // Refresh every minute
      revalidateOnFocus: false,
    }
  )

  return {
    data,
    error,
    isLoading,
  }
}

export function useMarketIndices() {
  const { data, error, isLoading } = useSWR(
    `${API_BASE_URL}/api/stocks/indices`,
    fetcher,
    {
      refreshInterval: 300000, // Refresh every 5 minutes
    }
  )

  return {
    indices: data || [],
    error,
    isLoading,
  }
}

export function useTopCryptos(limit: number = 10) {
  const { data, error, isLoading } = useSWR(
    `${API_BASE_URL}/api/crypto/top/${limit}`,
    fetcher,
    {
      refreshInterval: 180000, // Refresh every 3 minutes
    }
  )

  return {
    cryptos: data || [],
    error,
    isLoading,
  }
}

export function useLatestNews(limit: number = 20) {
  const { data, error, isLoading } = useSWR(
    `${API_BASE_URL}/api/news/latest?limit=${limit}`,
    fetcher,
    {
      refreshInterval: 900000, // Refresh every 15 minutes
    }
  )

  return {
    news: data || [],
    error,
    isLoading,
  }
}