'use client'

import { useState, useEffect } from 'react'
import { TrendingUpIcon, TrendingDownIcon, MinusIcon } from 'lucide-react'

interface SentimentData {
  score: number
  classification: 'bullish' | 'bearish' | 'neutral'
  confidence: number
  sources_count?: number
}

interface SentimentIndicatorProps {
  symbol: string
  className?: string
}

export default function SentimentIndicator({ symbol, className = '' }: SentimentIndicatorProps) {
  const [sentiment, setSentiment] = useState<SentimentData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch sentiment data when component mounts or symbol changes

  useEffect(() => {
    fetchSentiment()
  }, [symbol])

  const fetchSentiment = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/sentiment/combined/${symbol}`)
      if (!response.ok) throw new Error('Failed to fetch sentiment')
      
      const data = await response.json()
      if (data.combined_sentiment) {
        setSentiment(data.combined_sentiment)
      } else {
        setError('No sentiment data available')
      }
    } catch (err) {
      setError('Failed to load sentiment')
      console.error('Sentiment fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getSentimentColor = (classification: string) => {
    switch (classification) {
      case 'bullish':
        return 'text-green-600 bg-green-50'
      case 'bearish':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getSentimentIcon = (classification: string) => {
    switch (classification) {
      case 'bullish':
        return <TrendingUpIcon className="w-4 h-4" />
      case 'bearish':
        return <TrendingDownIcon className="w-4 h-4" />
      default:
        return <MinusIcon className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-8 bg-gray-100 rounded"></div>
      </div>
    )
  }

  if (error || !sentiment) {
    return (
      <div className={`text-xs text-gray-500 ${className}`}>
        Sentiment unavailable
      </div>
    )
  }

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(sentiment.classification)}`}>
        {getSentimentIcon(sentiment.classification)}
        <span className="ml-1 capitalize">{sentiment.classification}</span>
      </div>
      <div className="text-xs text-gray-500">
        {Math.abs(sentiment.score).toFixed(2)} ({(sentiment.confidence * 100).toFixed(0)}%)
      </div>
      {sentiment.sources_count && (
        <div className="text-xs text-gray-400">
          {sentiment.sources_count} sources
        </div>
      )}
    </div>
  )
}