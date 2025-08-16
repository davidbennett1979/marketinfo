'use client'

import React, { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronUp, Send, Sparkles, AlertCircle, ExternalLink, Plus, TrendingUp } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { User } from '@supabase/supabase-js'
import { authenticatedFetch } from '@/lib/auth'
import ReactMarkdown from 'react-markdown'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  actions?: Action[]
  provider?: string
  timestamp: Date
  error?: boolean
}

interface Source {
  title: string
  url: string
}

interface Action {
  type: 'add_to_watchlist' | 'view_technical'
  symbol: string
  label: string
}

interface ChatUsage {
  requests_last_hour: number
  limit_per_hour: number
  remaining: number
}

export default function ChatInterface() {
  const [isExpanded, setIsExpanded] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [usage, setUsage] = useState<ChatUsage | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const supabase = createClient()

  // Get user on mount
  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
    }
    getUser()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [supabase])

  // Keyboard shortcut
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsExpanded(true)
        setTimeout(() => inputRef.current?.focus(), 100)
      }
    }
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Fetch usage on mount
  useEffect(() => {
    if (user) {
      fetchUsage()
    }
  }, [user])

  const fetchUsage = async () => {
    try {
      const response = await authenticatedFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ai/usage`)
      if (response.ok) {
        const data = await response.json()
        setUsage(data)
      }
    } catch (error) {
      console.error('Failed to fetch usage:', error)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Get current context
      const context = {
        current_view: window.location.pathname,
        // Add more context as needed
      }

      const response = await authenticatedFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content,
          context,
          stream: false // For now, we'll handle streaming later
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.content,
        sources: data.sources,
        actions: data.actions,
        provider: data.provider,
        timestamp: new Date(),
        error: data.error
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Refresh usage
      fetchUsage()

    } catch (error) {
      console.error('Chat error:', error)
      let errorContent = 'Sorry, I encountered an error processing your request. Please try again.'
      
      if (error instanceof Error) {
        errorContent = `Error: ${error.message}`
      }
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: errorContent,
        timestamp: new Date(),
        error: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleAction = async (action: Action) => {
    if (action.type === 'add_to_watchlist') {
      try {
        const response = await authenticatedFetch(`${process.env.NEXT_PUBLIC_API_URL}/api/watchlist`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ symbol: action.symbol })
        })

        if (response.ok) {
          // Show success feedback
          alert(`Added ${action.symbol} to watchlist`)
        }
      } catch (error) {
        console.error('Failed to add to watchlist:', error)
      }
    } else if (action.type === 'view_technical') {
      // Navigate to technical analysis view
      window.location.href = `/technical?symbol=${action.symbol}`
    }
  }

  const suggestedQueries = [
    "Why did NVDA stock jump today?",
    "What's the latest news on AAPL?",
    "Analyze my watchlist portfolio",
    "Compare TSLA vs traditional automakers",
    "What are the upcoming earnings this week?"
  ]

  return (
    <div className="fixed top-16 left-0 right-0 z-40 bg-gray-900 border-b border-gray-800 shadow-lg">
      <div 
        className="flex items-center justify-between px-4 py-2 cursor-pointer hover:bg-gray-800 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-medium text-gray-300">
            AI Assistant - Ask about markets, stocks, or your portfolio
          </span>
          <span className="text-xs text-gray-500">(Cmd/Ctrl + K)</span>
        </div>
        <div className="flex items-center gap-4">
          {usage && (
            <span className="text-xs text-gray-500">
              {usage.remaining}/{usage.limit_per_hour} queries remaining
            </span>
          )}
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-gray-800">
          <div className="max-w-4xl mx-auto p-4">
            {/* Messages */}
            <div className="max-h-96 overflow-y-auto mb-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">Start a conversation or try one of these:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {suggestedQueries.map((query, index) => (
                      <button
                        key={index}
                        onClick={() => setInput(query)}
                        className="px-3 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                      >
                        {query}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-2xl p-3 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.error
                        ? 'bg-red-900 text-red-100'
                        : 'bg-gray-800 text-gray-200'
                    }`}
                  >
                    {message.role === 'assistant' && message.provider && (
                      <div className="text-xs text-gray-500 mb-1">
                        via {message.provider}
                      </div>
                    )}
                    
                    <div className="prose prose-sm prose-invert max-w-none">
                      <ReactMarkdown>
                        {message.content}
                      </ReactMarkdown>
                    </div>

                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-700">
                        <p className="text-xs text-gray-400 mb-2">Sources:</p>
                        <div className="space-y-1">
                          {message.sources.map((source, index) => (
                            <a
                              key={index}
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                            >
                              <ExternalLink className="w-3 h-3" />
                              {source.title}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    {message.actions && message.actions.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-700">
                        <div className="flex flex-wrap gap-2">
                          {message.actions.map((action, index) => (
                            <button
                              key={index}
                              onClick={() => handleAction(action)}
                              className="flex items-center gap-1 px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                            >
                              {action.type === 'add_to_watchlist' ? (
                                <Plus className="w-3 h-3" />
                              ) : (
                                <TrendingUp className="w-3 h-3" />
                              )}
                              {action.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-800 p-3 rounded-lg">
                    <div className="flex items-center gap-2">
                      <div className="animate-pulse flex gap-1">
                        <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                        <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                        <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                      </div>
                      <span className="text-sm text-gray-400">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Ask about stocks, markets, or your portfolio..."
                className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500 text-gray-200 placeholder-gray-500"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>

            {usage && usage.remaining < 5 && (
              <div className="mt-2 flex items-center gap-1 text-xs text-yellow-500">
                <AlertCircle className="w-3 h-3" />
                Low on queries: {usage.remaining} remaining this hour
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}