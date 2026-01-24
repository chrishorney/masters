/** Update indicator component for real-time updates */
import { useEffect, useState } from 'react'

interface UpdateIndicatorProps {
  lastUpdated?: string
  isRefetching?: boolean
}

export function UpdateIndicator({ lastUpdated, isRefetching }: UpdateIndicatorProps) {
  const [timeAgo, setTimeAgo] = useState<string>('')
  const [formattedTime, setFormattedTime] = useState<string>('')

  useEffect(() => {
    if (!lastUpdated) return

    const updateTimeAgo = () => {
      const now = new Date()
      const updated = new Date(lastUpdated)
      const diffMs = now.getTime() - updated.getTime()
      const diffSec = Math.floor(diffMs / 1000)
      const diffMin = Math.floor(diffSec / 60)

      if (diffSec < 10) {
        setTimeAgo('Just now')
      } else if (diffSec < 60) {
        setTimeAgo(`${diffSec}s ago`)
      } else if (diffMin < 60) {
        setTimeAgo(`${diffMin}m ago`)
      } else {
        const diffHour = Math.floor(diffMin / 60)
        setTimeAgo(`${diffHour}h ago`)
      }

      // Format the actual timestamp
      const formatted = updated.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
      setFormattedTime(formatted)
    }

    updateTimeAgo()
    const interval = setInterval(updateTimeAgo, 1000)

    return () => clearInterval(interval)
  }, [lastUpdated])

  if (isRefetching) {
    return (
      <div className="flex items-center space-x-2 text-sm text-gray-600">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        <span>Updating...</span>
      </div>
    )
  }

  if (!lastUpdated) return null

  return (
    <div className="flex items-center space-x-2 text-sm text-gray-500" title={formattedTime ? `Last synced: ${formattedTime}` : ''}>
      <div className="w-2 h-2 bg-green-500 rounded-full" />
      <span>
        Updated {timeAgo}
        {formattedTime && (
          <span className="ml-2 text-xs text-gray-400">
            ({formattedTime})
          </span>
        )}
      </span>
    </div>
  )
}
