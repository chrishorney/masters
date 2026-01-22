/** Tournament management section */
import { useState } from 'react'
import { useCalculateScores } from '../../hooks/useTournament'
import { tournamentApi } from '../../services/api'
import api from '../../services/api'
import type { Tournament } from '../../types'

interface TournamentManagementSectionProps {
  tournament: Tournament
}

export function TournamentManagementSection({ tournament }: TournamentManagementSectionProps) {
  const [syncing, setSyncing] = useState(false)
  const [calculating, setCalculating] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  
  const calculateScores = useCalculateScores()

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
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Sync & Calculate (One-Time)</h3>
            <p className="text-sm text-gray-600 mb-3">
              Sync tournament data and calculate scores in one action
            </p>
            <button
              onClick={handleRunJobOnce}
              disabled={calculating}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {calculating ? 'Running...' : 'Sync & Calculate'}
            </button>
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
