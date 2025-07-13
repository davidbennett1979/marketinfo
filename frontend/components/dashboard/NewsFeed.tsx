'use client'

import { useLatestNews } from '@/hooks/useMarketData'
import { ExternalLinkIcon, ClockIcon } from 'lucide-react'

export default function NewsFeed() {
  const { news, error, isLoading } = useLatestNews(10)

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Latest News</h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Latest News</h2>
        <p className="text-red-500">Failed to load news</p>
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Latest News</h2>
      <div className="space-y-3">
        {news.map((article: any, index: number) => (
          <div key={index} className="border-b last:border-0 pb-3 last:pb-0">
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group hover:bg-gray-50 -mx-2 px-2 py-1 rounded block"
            >
              <h3 className="font-medium text-sm group-hover:text-blue-600 line-clamp-2">
                {article.title}
              </h3>
              <div className="flex items-center justify-between mt-1">
                <div className="flex items-center text-xs text-gray-500">
                  <span className="font-medium">{article.source}</span>
                  <span className="mx-2">•</span>
                  <ClockIcon className="w-3 h-3 mr-1" />
                  <span>{formatDate(article.published_at)}</span>
                </div>
                <ExternalLinkIcon className="w-3 h-3 text-gray-400 group-hover:text-blue-600" />
              </div>
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}