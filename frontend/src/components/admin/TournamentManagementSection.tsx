/** Tournament management section */
import { useState, useEffect } from 'react'
import { useCalculateScores } from '../../hooks/useTournament'
import { tournamentApi, adminApi } from '../../services/api'
import api from '../../services/api'
import type { Tournament } from '../../types'

interface TournamentManagementSectionProps {
  tournament: Tournament
}

export function TournamentManagementSection({ tournament }: TournamentManagementSectionProps) {
  const [syncing, setSyncing] = useState(false)
  const [calculating, setCalculating] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [backgroundJobRunning, setBackgroundJobRunning] = useState(false)
  const [checkingStatus, setCheckingStatus] = useState(true)
  const [intervalSeconds, setIntervalSeconds] = useState(300) // Default 5 minutes
  const [startHour, setStartHour] = useState(6) // Default 6 AM
  const [stopHour, setStopHour] = useState(23) // Default 11 PM
  const [activeHours, setActiveHours] = useState<string>('')
  
  const calculateScores = useCalculateScores()

  // Check background job status on mount and periodically
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await adminApi.getBackgroundJobStatus(tournament.id)
        setBackgroundJobRunning(status.running)
        if (status.running && status.start_hour !== undefined && status.stop_hour !== undefined) {
          setStartHour(status.start_hour)
          setStopHour(status.stop_hour)
          setActiveHours(status.active_hours || `${status.start_hour}:00 - ${status.stop_hour}:59`)
        }
      } catch (error) {
        console.error('Failed to check background job status:', error)
      } finally {
        setCheckingStatus(false)
      }
    }

    checkStatus()
    // Check status every 10 seconds
    const interval = setInterval(checkStatus, 10000)
    return () => clearInterval(interval)
  }, [tournament.id])

  const handleSync = async () => {
    setSyncing(true)
    setMessage(null)

    try {
      await tournamentApi.sync(
        tournament.org_id || undefined,
        tournament.tourn_id,
        tournament.year
      )
      setMessage({ type: 'success', text: 'Tournament data synced successfully!' })
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to sync tournament' 
      })
    } finally {
      setSyncing(false)
    }
  }

  const handleCalculateScores = async () => {
    setCalculating(true)
    setMessage(null)

    try {
      await calculateScores.mutateAsync({ tournamentId: tournament.id })
      setMessage({ type: 'success', text: 'Scores calculated successfully!' })
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to calculate scores' 
      })
    } finally {
      setCalculating(false)
    }
  }

  const handleRunJobOnce = async () => {
    setCalculating(true)
    setMessage(null)

    try {
      await api.post('/admin/jobs/run-once', null, {
        params: { tournament_id: tournament.id }
      })
      setMessage({ type: 'success', text: 'Background job executed successfully!' })
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to run job' 
      })
    } finally {
      setCalculating(false)
    }
  }

  const handleStartBackgroundJob = async () => {
    setCalculating(true)
    setMessage(null)

    try {
      const result = await adminApi.startBackgroundJob(tournament.id, intervalSeconds, startHour, stopHour)
      setBackgroundJobRunning(true)
      setActiveHours(result.active_hours || `${startHour}:00 - ${stopHour}:59`)
      setMessage({ 
        type: 'success', 
        text: `Automatic sync started! Will sync every ${intervalSeconds} seconds (${Math.round(intervalSeconds / 60)} minutes) during ${result.active_hours || `${startHour}:00 - ${stopHour}:59`}.` 
      })
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to start background job' 
      })
    } finally {
      setCalculating(false)
    }
  }

  const handleStopBackgroundJob = async () => {
    setCalculating(true)
    setMessage(null)

    try {
      await adminApi.stopBackgroundJob(tournament.id)
      setBackgroundJobRunning(false)
      setMessage({ type: 'success', text: 'Automatic sync stopped.' })
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to stop background job' 
      })
    } finally {
      setCalculating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Tournament Info */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Tournament Information</h2>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Name</dt>
            <dd className="mt-1 text-sm text-gray-900">{tournament.name}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Year</dt>
            <dd className="mt-1 text-sm text-gray-900">{tournament.year}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Current Round</dt>
            <dd className="mt-1 text-sm text-gray-900">{tournament.current_round}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd className="mt-1 text-sm text-gray-900">{tournament.status}</dd>
          </div>
        </dl>
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Tournament Actions</h2>
        
        <div className="space-y-4">
          {/* Sync Tournament */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="font-medium text-gray-900 mb-2">Sync Tournament Data</h3>
            <p className="text-sm text-gray-600 mb-3">
              Fetch latest leaderboard and scorecard data from Slash Golf API
            </p>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {syncing ? 'Syncing...' : 'Sync Tournament Data'}
            </button>
          </div>

          {/* Calculate Scores */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="font-medium text-gray-900 mb-2">Calculate Scores</h3>
            <p className="text-sm text-gray-600 mb-3">
              Recalculate scores for all entries based on current leaderboard data
            </p>
            <button
              onClick={handleCalculateScores}
              disabled={calculating}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {calculating ? 'Calculating...' : 'Calculate Scores'}
            </button>
          </div>

          {/* Run Job Once */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="font-medium text-gray-900 mb-2">Sync & Calculate (One-Time)</h3>
            <p className="text-sm text-gray-600 mb-3">
              Sync tournament data and calculate scores in one action
            </p>
            <button
              onClick={handleRunJobOnce}
              disabled={calculating || backgroundJobRunning}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {calculating ? 'Running...' : 'Sync & Calculate'}
            </button>
          </div>

          {/* Automatic Background Sync */}
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Automatic Background Sync</h3>
            <p className="text-sm text-gray-600 mb-3">
              Automatically sync tournament data and calculate scores at regular intervals. 
              <span className="font-semibold text-orange-600"> Use with caution to avoid exceeding API rate limits.</span>
            </p>
            
            {/* Status Indicator */}
            <div className="mb-4 p-3 rounded-lg bg-gray-50 border border-gray-200">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${backgroundJobRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
                <span className="text-sm font-medium text-gray-700">
                  Status: {backgroundJobRunning ? 'Running' : 'Stopped'}
                </span>
                {checkingStatus && (
                  <span className="text-xs text-gray-500">(checking...)</span>
                )}
              </div>
              {backgroundJobRunning && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-gray-600">
                    Syncing every {intervalSeconds} seconds ({Math.round(intervalSeconds / 60)} minutes)
                  </p>
                  {activeHours && (
                    <p className="text-xs text-gray-600">
                      Active hours: {activeHours}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Interval Configuration */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sync Interval (seconds)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="60"
                  max="3600"
                  step="60"
                  value={intervalSeconds}
                  onChange={(e) => setIntervalSeconds(parseInt(e.target.value) || 300)}
                  disabled={backgroundJobRunning}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed w-32"
                />
                <span className="text-sm text-gray-600">
                  ({Math.round(intervalSeconds / 60)} minutes)
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Recommended: 300+ seconds (5+ minutes) to avoid rate limits. Minimum: 60 seconds.
              </p>
            </div>

            {/* Active Hours Configuration */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Active Hours (24-hour format)
              </label>
              <p className="text-xs text-gray-600 mb-3">
                Sync will only run during these hours. Outside these hours, syncs are paused to save API calls.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Start Hour</label>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={startHour}
                    onChange={(e) => setStartHour(parseInt(e.target.value) || 6)}
                    disabled={backgroundJobRunning}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed w-full"
                  />
                  <span className="text-xs text-gray-500 mt-1 block">
                    {startHour === 0 ? '12 AM' : startHour < 12 ? `${startHour} AM` : startHour === 12 ? '12 PM' : `${startHour - 12} PM`}
                  </span>
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Stop Hour</label>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={stopHour}
                    onChange={(e) => setStopHour(parseInt(e.target.value) || 23)}
                    disabled={backgroundJobRunning}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed w-full"
                  />
                  <span className="text-xs text-gray-500 mt-1 block">
                    {stopHour === 0 ? '12 AM' : stopHour < 12 ? `${stopHour} AM` : stopHour === 12 ? '12 PM' : `${stopHour - 12} PM`}
                  </span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Example: Start 6, Stop 23 = Active from 6 AM to 11:59 PM (pauses midnight-6 AM)
              </p>
            </div>

            {/* Start/Stop Buttons */}
            <div className="flex gap-2">
              {!backgroundJobRunning ? (
                <button
                  onClick={handleStartBackgroundJob}
                  disabled={calculating || checkingStatus}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {calculating ? 'Starting...' : 'Start Automatic Sync'}
                </button>
              ) : (
                <button
                  onClick={handleStopBackgroundJob}
                  disabled={calculating}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {calculating ? 'Stopping...' : 'Stop Automatic Sync'}
                </button>
              )}
            </div>

            {/* Rate Limit Warning */}
            <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-xs text-yellow-800">
                <strong>⚠️ Rate Limit Warning:</strong> Each sync makes multiple API calls. 
                With a {Math.round(intervalSeconds / 60)}-minute interval, you'll make approximately {Math.round((24 * 60) / (intervalSeconds / 60))} syncs per day. 
                Monitor your RapidAPI usage to avoid exceeding limits.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      {message && (
        <div className={`rounded-lg p-4 ${
          message.type === 'success' 
            ? 'bg-green-50 border border-green-200 text-green-800'
            : 'bg-red-50 border border-red-200 text-red-800'
        }`}>
          {message.text}
        </div>
      )}
    </div>
  )
}
