/** Ranking history page */
import { useState } from 'react'
import { useCurrentTournament } from '../hooks/useTournament'
import { useTournamentRankingHistory, useRankingAnalytics } from '../hooks/useRankingHistory'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { PositionChart } from '../components/ranking/PositionChart'
import { RankingAnalytics } from '../components/ranking/RankingAnalytics'

export function RankingHistoryPage() {
  const { data: tournament, isLoading: tournamentLoading } = useCurrentTournament()
  const [selectedRound, setSelectedRound] = useState<number | undefined>(undefined)
  
  const {
    data: rankingData,
    isLoading: rankingLoading,
    error: rankingError,
    refetch
  } = useTournamentRankingHistory(tournament?.id, selectedRound)
  
  const {
    data: analytics,
    isLoading: analyticsLoading
  } = useRankingAnalytics(tournament?.id)

  if (tournamentLoading || rankingLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (rankingError || !rankingData) {
    return (
      <div className="max-w-6xl mx-auto">
        <ErrorMessage 
          message="Failed to load ranking history. Please try again later."
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  const { snapshots, tournament: tournamentInfo } = rankingData

  // Create entry name map
  const entryNames: Record<number, string> = {}
  snapshots.forEach(snapshot => {
    if (!entryNames[snapshot.entry_id]) {
      entryNames[snapshot.entry_id] = snapshot.entry_name
    }
  })

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
          Ranking History
        </h1>
        <p className="text-gray-600">
          Track how entries' positions changed throughout {tournamentInfo.name}
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <label className="text-sm font-medium text-gray-700">
            Filter by Round:
          </label>
          <select
            value={selectedRound || ''}
            onChange={(e) => setSelectedRound(e.target.value ? parseInt(e.target.value) : undefined)}
            className="px-3 py-2 rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
          >
            <option value="">All Rounds</option>
            <option value="1">Round 1</option>
            <option value="2">Round 2</option>
            <option value="3">Round 3</option>
            <option value="4">Round 4</option>
          </select>
          <div className="text-sm text-gray-600">
            {snapshots.length} snapshot{snapshots.length !== 1 ? 's' : ''} recorded
          </div>
        </div>
      </div>

      {/* Position Chart */}
      {snapshots.length > 0 && (
        <div className="mb-6">
          <PositionChart snapshots={snapshots} entryNames={entryNames} />
        </div>
      )}

      {/* Analytics */}
      {!analyticsLoading && analytics && (
        <RankingAnalytics analytics={analytics} />
      )}

      {/* Empty State */}
      {snapshots.length === 0 && (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-500 mb-4">
            No ranking history available yet.
          </p>
          <p className="text-sm text-gray-400">
            Ranking snapshots are created automatically when scores are calculated.
            Try calculating scores to start tracking position changes.
          </p>
        </div>
      )}
    </div>
  )
}
