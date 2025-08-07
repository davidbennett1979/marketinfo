'use client'

import { useState, useRef, useEffect, useCallback, ReactNode } from 'react'
import { InfoIcon, TrendingUpIcon, TrendingDownIcon, CalendarIcon, DollarSignIcon, BarChart3Icon } from 'lucide-react'

interface TooltipPosition {
  top: number
  left: number
  placement: 'top' | 'bottom' | 'left' | 'right'
}

interface SmartTooltipProps {
  children: ReactNode
  content: ReactNode | string
  title?: string
  type?: 'info' | 'financial' | 'sentiment' | 'technical' | 'earnings' | 'news'
  delay?: number
  maxWidth?: number
  className?: string
  disabled?: boolean
}

interface FinancialTooltipProps {
  symbol: string
  price?: number
  change?: number
  changePercent?: number
  volume?: number
  marketCap?: number
  pe?: number
  dividend?: number
  lastUpdate?: string
}

interface SentimentTooltipProps {
  symbol: string
  sentiment: 'bullish' | 'bearish' | 'neutral'
  score: number
  confidence: number
  rationale: string
  postCount: number
  source: string
}

interface TechnicalTooltipProps {
  symbol: string
  rsi?: number
  macd?: { macd: number; signal: number; histogram: number }
  support?: number
  resistance?: number
  trend: 'bullish' | 'bearish' | 'neutral'
  signal: string
}

interface EarningsTooltipProps {
  symbol: string
  date: string
  time: 'pre-market' | 'after-market'
  estimate?: number
  previous?: number
  surprise?: number
}

export default function SmartTooltip({ 
  children, 
  content, 
  title, 
  type = 'info',
  delay = 300,
  maxWidth = 300,
  className = '',
  disabled = false
}: SmartTooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState<TooltipPosition>({ top: 0, left: 0, placement: 'top' })
  const triggerRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const calculatePosition = useCallback(() => {
    if (!triggerRef.current || !tooltipRef.current) return

    const triggerRect = triggerRef.current.getBoundingClientRect()
    const tooltipRect = tooltipRef.current.getBoundingClientRect()
    const viewport = { width: window.innerWidth, height: window.innerHeight }
    
    let top = triggerRect.top - tooltipRect.height - 8
    let left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
    let placement: TooltipPosition['placement'] = 'top'

    // Adjust horizontal position if tooltip goes off screen
    if (left < 8) {
      left = 8
    } else if (left + tooltipRect.width > viewport.width - 8) {
      left = viewport.width - tooltipRect.width - 8
    }

    // If tooltip goes above viewport, place it below
    if (top < 8) {
      top = triggerRect.bottom + 8
      placement = 'bottom'
    }

    // If tooltip goes below viewport, try left/right placement
    if (top + tooltipRect.height > viewport.height - 8) {
      const leftSpace = triggerRect.left
      const rightSpace = viewport.width - triggerRect.right
      
      if (Math.max(leftSpace, rightSpace) > tooltipRect.width + 16) {
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
        if (leftSpace > rightSpace) {
          left = triggerRect.left - tooltipRect.width - 8
          placement = 'left'
        } else {
          left = triggerRect.right + 8
          placement = 'right'
        }
      }
    }

    setPosition({ top, left, placement })
  }, [])

  const handleMouseEnter = () => {
    if (disabled) return
    
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true)
      setTimeout(calculatePosition, 0) // Allow tooltip to render first
    }, delay)
  }

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(false)
  }

  useEffect(() => {
    if (isVisible) {
      calculatePosition()
      const handleResize = () => calculatePosition()
      const handleScroll = () => setIsVisible(false)
      
      window.addEventListener('resize', handleResize)
      window.addEventListener('scroll', handleScroll, true)
      
      return () => {
        window.removeEventListener('resize', handleResize)
        window.removeEventListener('scroll', handleScroll, true)
      }
    }
  }, [isVisible, calculatePosition])

  const getTypeIcon = () => {
    switch (type) {
      case 'financial': return <DollarSignIcon className="w-4 h-4" />
      case 'sentiment': return <BarChart3Icon className="w-4 h-4" />
      case 'technical': return <TrendingUpIcon className="w-4 h-4" />
      case 'earnings': return <CalendarIcon className="w-4 h-4" />
      case 'news': return <InfoIcon className="w-4 h-4" />
      default: return <InfoIcon className="w-4 h-4" />
    }
  }

  const getTypeColor = () => {
    switch (type) {
      case 'financial': return 'text-blue-500'
      case 'sentiment': return 'text-purple-500'
      case 'technical': return 'text-green-500'
      case 'earnings': return 'text-orange-500'
      case 'news': return 'text-gray-500'
      default: return 'text-blue-500'
    }
  }

  if (disabled) {
    return <>{children}</>
  }

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className={`inline-block cursor-help ${className}`}
      >
        {children}
      </div>

      {isVisible && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40 pointer-events-none"
            onClick={() => setIsVisible(false)}
          />
          
          {/* Tooltip */}
          <div
            ref={tooltipRef}
            className={`fixed z-50 bg-gray-900 text-white text-sm rounded-lg shadow-2xl border border-gray-700 animate-in fade-in-0 zoom-in-95 duration-200 ${
              position.placement === 'top' ? 'slide-in-from-bottom-2' :
              position.placement === 'bottom' ? 'slide-in-from-top-2' :
              position.placement === 'left' ? 'slide-in-from-right-2' :
              'slide-in-from-left-2'
            }`}
            style={{
              top: position.top,
              left: position.left,
              maxWidth: `${maxWidth}px`,
              pointerEvents: 'auto'
            }}
          >
            {/* Arrow */}
            <div
              className={`absolute w-2 h-2 bg-gray-900 border border-gray-700 rotate-45 ${
                position.placement === 'top' ? '-bottom-1 left-1/2 -translate-x-1/2 border-t-0 border-l-0' :
                position.placement === 'bottom' ? '-top-1 left-1/2 -translate-x-1/2 border-b-0 border-r-0' :
                position.placement === 'left' ? '-right-1 top-1/2 -translate-y-1/2 border-l-0 border-t-0' :
                '-left-1 top-1/2 -translate-y-1/2 border-r-0 border-b-0'
              }`}
            />
            
            <div className="p-3">
              {title && (
                <div className={`flex items-center mb-2 pb-2 border-b border-gray-700 ${getTypeColor()}`}>
                  {getTypeIcon()}
                  <span className="ml-2 font-semibold">{title}</span>
                </div>
              )}
              <div className="text-gray-200 leading-relaxed">
                {content}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}

// Specialized tooltip components
export function FinancialTooltip({ 
  symbol, 
  price, 
  change, 
  changePercent, 
  volume, 
  marketCap, 
  pe, 
  dividend,
  lastUpdate,
  children
}: FinancialTooltipProps & { children: ReactNode }) {
  const formatPrice = (value?: number) => {
    if (!value) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  const formatLargeNumber = (value?: number) => {
    if (!value) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      notation: 'compact',
      compactDisplay: 'short'
    }).format(value)
  }

  const formatPercent = (value?: number) => {
    if (!value) return 'N/A'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  const content = (
    <div className="space-y-2">
      {price && (
        <div className="flex justify-between">
          <span className="text-gray-300">Price:</span>
          <span className="font-semibold">{formatPrice(price)}</span>
        </div>
      )}
      
      {(change !== undefined || changePercent !== undefined) && (
        <div className="flex justify-between">
          <span className="text-gray-300">Change:</span>
          <div className={`font-semibold ${(change && change >= 0) || (changePercent && changePercent >= 0) ? 'text-green-400' : 'text-red-400'}`}>
            {change && formatPrice(Math.abs(change))} {changePercent && `(${formatPercent(changePercent)})`}
          </div>
        </div>
      )}
      
      {volume && (
        <div className="flex justify-between">
          <span className="text-gray-300">Volume:</span>
          <span>{formatLargeNumber(volume)}</span>
        </div>
      )}
      
      {marketCap && (
        <div className="flex justify-between">
          <span className="text-gray-300">Market Cap:</span>
          <span>{formatLargeNumber(marketCap)}</span>
        </div>
      )}
      
      {pe && (
        <div className="flex justify-between">
          <span className="text-gray-300">P/E Ratio:</span>
          <span>{pe.toFixed(2)}</span>
        </div>
      )}
      
      {dividend && (
        <div className="flex justify-between">
          <span className="text-gray-300">Dividend:</span>
          <span>{formatPrice(dividend)}</span>
        </div>
      )}
      
      {lastUpdate && (
        <div className="text-xs text-gray-400 pt-2 border-t border-gray-700">
          Updated: {new Date(lastUpdate).toLocaleString()}
        </div>
      )}
    </div>
  )

  return (
    <SmartTooltip
      title={`${symbol} Financial Data`}
      content={content}
      type="financial"
      maxWidth={280}
    >
      {children}
    </SmartTooltip>
  )
}

export function SentimentTooltip({
  symbol,
  sentiment,
  score,
  confidence,
  rationale,
  postCount,
  source,
  children
}: SentimentTooltipProps & { children: ReactNode }) {
  const getSentimentColor = () => {
    switch (sentiment) {
      case 'bullish': return 'text-green-400'
      case 'bearish': return 'text-red-400'
      default: return 'text-yellow-400'
    }
  }

  const getSentimentIcon = () => {
    switch (sentiment) {
      case 'bullish': return <TrendingUpIcon className="w-4 h-4" />
      case 'bearish': return <TrendingDownIcon className="w-4 h-4" />
      default: return <BarChart3Icon className="w-4 h-4" />
    }
  }

  const content = (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-gray-300">Sentiment:</span>
        <div className={`flex items-center font-semibold capitalize ${getSentimentColor()}`}>
          {getSentimentIcon()}
          <span className="ml-1">{sentiment}</span>
        </div>
      </div>
      
      <div className="flex justify-between">
        <span className="text-gray-300">Score:</span>
        <span className={`font-semibold ${getSentimentColor()}`}>
          {(score * 100).toFixed(0)}%
        </span>
      </div>
      
      <div className="flex justify-between">
        <span className="text-gray-300">Confidence:</span>
        <div className="flex items-center">
          <div className="w-16 h-2 bg-gray-600 rounded-full mr-2">
            <div 
              className={`h-2 rounded-full ${getSentimentColor().replace('text-', 'bg-')}`}
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
          <span className="text-sm">{(confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
      
      <div className="pt-2 border-t border-gray-700">
        <div className="text-gray-300 text-xs mb-1">Analysis:</div>
        <p className="text-sm">{rationale}</p>
      </div>
      
      <div className="flex justify-between text-xs text-gray-400">
        <span>{postCount} posts from {source}</span>
      </div>
    </div>
  )

  return (
    <SmartTooltip
      title={`${symbol} Sentiment Analysis`}
      content={content}
      type="sentiment"
      maxWidth={320}
    >
      {children}
    </SmartTooltip>
  )
}

export function TechnicalTooltip({
  symbol,
  rsi,
  macd,
  support,
  resistance,
  trend,
  signal,
  children
}: TechnicalTooltipProps & { children: ReactNode }) {
  const getTrendColor = () => {
    switch (trend) {
      case 'bullish': return 'text-green-400'
      case 'bearish': return 'text-red-400'
      default: return 'text-yellow-400'
    }
  }

  const content = (
    <div className="space-y-2">
      <div className="flex justify-between">
        <span className="text-gray-300">Trend:</span>
        <span className={`font-semibold capitalize ${getTrendColor()}`}>
          {trend}
        </span>
      </div>
      
      <div className="flex justify-between">
        <span className="text-gray-300">Signal:</span>
        <span className="font-semibold">{signal}</span>
      </div>
      
      {rsi && (
        <div className="flex justify-between">
          <span className="text-gray-300">RSI (14):</span>
          <span className={`font-semibold ${
            rsi >= 70 ? 'text-red-400' : rsi <= 30 ? 'text-green-400' : 'text-yellow-400'
          }`}>
            {rsi.toFixed(1)}
          </span>
        </div>
      )}
      
      {macd && (
        <div className="space-y-1">
          <div className="text-gray-300 text-xs">MACD:</div>
          <div className="flex justify-between text-sm">
            <span>Signal:</span>
            <span className={`${macd.histogram > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {macd.histogram > 0 ? 'Bullish' : 'Bearish'}
            </span>
          </div>
        </div>
      )}
      
      {(support || resistance) && (
        <div className="space-y-1 pt-2 border-t border-gray-700">
          {support && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Support:</span>
              <span className="text-green-400">${support.toFixed(2)}</span>
            </div>
          )}
          {resistance && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Resistance:</span>
              <span className="text-red-400">${resistance.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )

  return (
    <SmartTooltip
      title={`${symbol} Technical Analysis`}
      content={content}
      type="technical"
      maxWidth={280}
    >
      {children}
    </SmartTooltip>
  )
}

export function EarningsTooltip({
  symbol,
  date,
  time,
  estimate,
  previous,
  surprise,
  children
}: EarningsTooltipProps & { children: ReactNode }) {
  const content = (
    <div className="space-y-2">
      <div className="flex justify-between">
        <span className="text-gray-300">Date:</span>
        <span className="font-semibold">{new Date(date).toLocaleDateString()}</span>
      </div>
      
      <div className="flex justify-between">
        <span className="text-gray-300">Time:</span>
        <span className={`font-semibold ${
          time === 'pre-market' ? 'text-blue-400' : 'text-purple-400'
        }`}>
          {time === 'pre-market' ? 'Pre-Market' : 'After Market'}
        </span>
      </div>
      
      {estimate && (
        <div className="flex justify-between">
          <span className="text-gray-300">Estimate:</span>
          <span className="font-semibold">${estimate.toFixed(2)}</span>
        </div>
      )}
      
      {previous && (
        <div className="flex justify-between">
          <span className="text-gray-300">Previous:</span>
          <span>${previous.toFixed(2)}</span>
        </div>
      )}
      
      {surprise && (
        <div className="flex justify-between">
          <span className="text-gray-300">Surprise:</span>
          <span className={`font-semibold ${surprise > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {surprise > 0 ? '+' : ''}{(surprise * 100).toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  )

  return (
    <SmartTooltip
      title={`${symbol} Earnings`}
      content={content}
      type="earnings"
      maxWidth={250}
    >
      {children}
    </SmartTooltip>
  )
}