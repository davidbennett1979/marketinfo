'use client'

import { useState, useEffect } from 'react'
import { TrendingUpIcon, TrendingDownIcon, MessageCircleIcon, MessageSquareIcon } from 'lucide-react'

interface SentimentOverviewProps {
  className?: string
}

interface TrendingPost {
  title: string
  score: number
  num_comments: number
  symbols: string[]
  sentiment: {
    classification: string
    sentiment_score: number
  }
  mock_data?: boolean
}

export default function SentimentOverview({ className = '' }: SentimentOverviewProps) {
  const [trendingPosts, setTrendingPosts] = useState<TrendingPost[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchTrendingData()
  }, [])

  const fetchTrendingData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/sentiment/reddit/wsb/trending?limit=5`)
      if (!response.ok) throw new Error('Failed to fetch trending data')
      
      const data = await response.json()
      setTrendingPosts(data.slice(0, 5)) // Top 5 posts
    } catch (err) {
      setError('Failed to load sentiment data')
      console.error('Sentiment fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getSentimentColor = (classification: string) => {
    switch (classification) {
      case 'bullish':
        return 'text-green-600'
      case 'bearish':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getSentimentIcon = (classification: string) => {
    switch (classification) {
      case 'bullish':
        return <TrendingUpIcon className="w-3 h-3" />
      case 'bearish':
        return <TrendingDownIcon className="w-3 h-3" />
      default:
        return <MessageCircleIcon className="w-3 h-3" />
    }
  }

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <MessageSquareIcon className="w-5 h-5 mr-2 text-orange-500" />
          Social Sentiment
        </h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <MessageSquareIcon className="w-5 h-5 mr-2 text-orange-500" />
          Social Sentiment
        </h2>
        <p className="text-red-500 text-sm">Failed to load sentiment data</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <MessageSquareIcon className="w-5 h-5 mr-2 text-orange-500" />
        Social Sentiment
      </h2>
      
      <div className="space-y-3">
        {trendingPosts.map((post, index) => (
          <div key={index} className="border-b last:border-0 pb-3 last:pb-0">
            <div className="flex items-start justify-between">
              <div className="flex-1 pr-2">
                <h3 className="text-sm font-medium line-clamp-2 mb-1">
                  {post.title}
                </h3>
                <div className="flex items-center space-x-3 text-xs text-gray-500">
                  <span className="flex items-center">
                    <TrendingUpIcon className="w-3 h-3 mr-1" />
                    {post.score}
                  </span>
                  <span className="flex items-center">
                    <MessageCircleIcon className="w-3 h-3 mr-1" />
                    {post.num_comments}
                  </span>
                  {post.symbols.length > 0 && (
                    <span className="font-medium">
                      {post.symbols.join(', ')}
                    </span>
                  )}
                </div>
              </div>
              <div className={`flex items-center text-xs ${getSentimentColor(post.sentiment.classification)}`}>
                {getSentimentIcon(post.sentiment.classification)}
                <span className="ml-1 capitalize font-medium">
                  {post.sentiment.classification}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Data from r/wallstreetbets</span>
          <span>Updated every 15 min</span>
        </div>
      </div>
    </div>
  )
}