/** Discord server widget component */
import { useState, useEffect } from 'react'
import { discordApi } from '../services/api'

export function DiscordWidget() {
  const [widgetUrl, setWidgetUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [iframeLoaded, setIframeLoaded] = useState(false)

  useEffect(() => {
    const fetchWidgetInfo = async () => {
      try {
        const response = await discordApi.getWidgetInfo()
        if (response.widget_url) {
          setWidgetUrl(response.widget_url)
        } else {
          setError('Widget URL not configured')
        }
      } catch (error: any) {
        console.error('Discord widget error:', error)
        setError(error.response?.status === 404 ? 'Discord widget not configured. Set DISCORD_SERVER_ID in Railway.' : 'Failed to load widget')
      } finally {
        setLoading(false)
      }
    }

    fetchWidgetInfo()
  }, [])

  // Timeout if iframe doesn't load within 10 seconds
  useEffect(() => {
    if (widgetUrl && !iframeLoaded) {
      const timeout = setTimeout(() => {
        if (!iframeLoaded) {
          setError('Widget is taking too long to load. Please check Discord server widget settings.')
        }
      }, 10000)
      return () => clearTimeout(timeout)
    }
  }, [widgetUrl, iframeLoaded])

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        <div className="flex items-center justify-center" style={{ minHeight: '400px' }}>
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#5865F2] mx-auto mb-2"></div>
            <p className="text-gray-500 text-sm">Loading Discord widget...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !widgetUrl) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        <div className="flex items-center gap-2 mb-4">
          <svg
            className="w-6 h-6 text-[#5865F2]"
            fill="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900">Live Updates</h3>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-600 mb-2">{error || 'Discord widget not available'}</p>
          <p className="text-xs text-gray-500">
            To enable: Set DISCORD_SERVER_ID in Railway and enable Server Widget in Discord settings
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
      <div className="flex items-center gap-2 mb-4">
        <svg
          className="w-6 h-6 text-[#5865F2]"
          fill="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
        </svg>
        <h3 className="text-lg font-semibold text-gray-900">Live Updates</h3>
      </div>
      {!iframeLoaded && (
        <div className="text-center py-4 mb-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5865F2] mx-auto mb-2"></div>
          <p className="text-gray-500 text-sm">Loading Discord server...</p>
        </div>
      )}
      <div className="w-full" style={{ minHeight: '400px' }}>
        <iframe
          src={widgetUrl}
          width="100%"
          height="400"
          allowTransparency={true}
          frameBorder="0"
          className="rounded-lg border-0"
          title="Discord Server Widget"
          onLoad={() => {
            setIframeLoaded(true)
            setError(null)
          }}
          onError={() => {
            setError('Failed to load Discord widget. Check server widget settings in Discord.')
            setIframeLoaded(false)
          }}
          style={{ border: 'none' }}
        />
      </div>
      {error && (
        <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Widget not loading?</strong> Make sure:
          </p>
          <ul className="text-xs text-yellow-700 mt-1 list-disc list-inside space-y-1">
            <li>Server Widget is enabled in Discord (Server Settings → Widget)</li>
            <li>DISCORD_SERVER_ID is set correctly in Railway</li>
            <li>Widget is enabled for the server</li>
          </ul>
        </div>
      )}
      <p className="text-xs text-gray-500 mt-2 text-center">
        Join our Discord server for live tournament updates and announcements
      </p>
    </div>
  )
}
