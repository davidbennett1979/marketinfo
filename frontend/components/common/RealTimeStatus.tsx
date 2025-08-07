'use client'

import { WifiIcon, WifiOffIcon, RefreshCwIcon, ClockIcon } from 'lucide-react'

interface RealTimeStatusProps {
  isConnected: boolean
  lastUpdate: Date | null
  onRefresh?: () => void
  className?: string
}

export default function RealTimeStatus({ 
  isConnected, 
  lastUpdate, 
  onRefresh, 
  className = '' 
}: RealTimeStatusProps) {
  const formatLastUpdate = (date: Date | null) => {
    if (!date) return 'Never'
    
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSeconds = Math.floor(diffMs / 1000)
    const diffMinutes = Math.floor(diffSeconds / 60)
    
    if (diffSeconds < 30) {
      return 'Just now'
    } else if (diffSeconds < 60) {
      return `${diffSeconds}s ago`
    } else if (diffMinutes < 60) {
      return `${diffMinutes}m ago`
    } else {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  }

  return (
    <div className={`flex items-center space-x-2 text-sm ${className}`}>
      {/* Connection Status */}
      <div className="flex items-center space-x-1">
        {isConnected ? (
          <>
            <WifiIcon className="w-4 h-4 text-green-500" />
            <span className="text-green-600 font-medium">Live</span>
          </>
        ) : (
          <>
            <WifiOffIcon className="w-4 h-4 text-red-500" />
            <span className="text-red-600 font-medium">Offline</span>
          </>
        )}
      </div>

      {/* Last Update Time */}
      <div className="flex items-center space-x-1 text-gray-500">
        <ClockIcon className="w-3 h-3" />
        <span className="text-xs">{formatLastUpdate(lastUpdate)}</span>
      </div>

      {/* Manual Refresh Button */}
      {onRefresh && (
        <button
          onClick={onRefresh}
          className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
          title="Refresh data"
        >
          <RefreshCwIcon className="w-3 h-3" />
        </button>
      )}
    </div>
  )
}

// Real-time pulse indicator
export function PulseIndicator({ isActive }: { isActive: boolean }) {
  return (
    <div className="flex items-center space-x-1">
      <div 
        className={`w-2 h-2 rounded-full ${
          isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
        }`} 
      />
      <span className="text-xs text-gray-500">
        {isActive ? 'Updating' : 'Paused'}
      </span>
    </div>
  )
}

// Connection quality indicator
export function ConnectionQuality({ 
  quality 
}: { 
  quality: 'excellent' | 'good' | 'poor' | 'offline' 
}) {
  const getQualityConfig = (quality: string) => {
    switch (quality) {
      case 'excellent':
        return { color: 'text-green-600', bars: 4, label: 'Excellent' }
      case 'good':
        return { color: 'text-yellow-600', bars: 3, label: 'Good' }
      case 'poor':
        return { color: 'text-red-600', bars: 2, label: 'Poor' }
      case 'offline':
        return { color: 'text-gray-400', bars: 0, label: 'Offline' }
      default:
        return { color: 'text-gray-400', bars: 0, label: 'Unknown' }
    }
  }

  const config = getQualityConfig(quality)

  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center space-x-0.5">
        {[1, 2, 3, 4].map((bar) => (
          <div
            key={bar}
            className={`w-1 h-3 rounded-sm ${
              bar <= config.bars
                ? config.color.replace('text-', 'bg-')
                : 'bg-gray-200'
            }`}
          />
        ))}
      </div>
      <span className={`text-xs ${config.color}`}>
        {config.label}
      </span>
    </div>
  )
}