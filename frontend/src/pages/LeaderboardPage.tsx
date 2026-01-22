/** Leaderboard page */
import { useCurrentTournament, useLeaderboard, useCalculateScores } from '../hooks/useTournament'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import type { LeaderboardEntry } from '../types'

export function LeaderboardPage() {
  const { data: tournament, isLoading: tournamentLoading } = useCurrentTournament()
  const { 
    data: leaderboardData, 
    isLoading: leaderboardLoading, 
    error: leaderboardError,
    refetch 
  } = useLeaderboard(tournament?.id)
  
  const calculateScores = useCalculateScores()

  const handleCalculateScores = async () => {
    if (!tournament) return
    await calculateScores.mutateAsync({ tournamentId: tournament.id })
  }

  if (tournamentLoading || leaderboardLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (leaderboardError || !leaderboardData) {
    return (
      <div className="max-w-4xl mx-auto">
        <ErrorMessage 
          message="Failed to load leaderboard. Please try again later."
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  const { entries, tournament: tournamentInfo } = leaderboardData

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Leaderboard
          </h1>
          <p className="text-gray-600">
            {tournamentInfo.name} • Round {tournamentInfo.current_round}
          </p>
        </div>
        <button
          onClick={handleCalculateScores}
          disabled={calculateScores.isPending}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {calculateScores.isPending ? 'Calculating...' : 'Recalculate Scores'}
        </button>
      </div>

      {/* Leaderboard Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-green-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Participant
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Points
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Base Points
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bonus Points
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {entries.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No entries found. Scores may need to be calculated.
                  </td>
                </tr>
              ) : (
                entries.map((entry: LeaderboardEntry, index: number) => (
                  <LeaderboardRow key={entry.entry.id} entry={entry} rank={index + 1} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Last Updated */}
      {leaderboardData.last_updated && (
        <div className="mt-4 text-sm text-gray-500 text-center">
          Last updated: {new Date(leaderboardData.last_updated).toLocaleString()}
        </div>
      )}
    </div>
  )
}

function LeaderboardRow({ entry, rank }: { entry: LeaderboardEntry; rank: number }) {
  const getRankBadge = (rank: number) => {
    if (rank === 1) return '🥇'
    if (rank === 2) return '🥈'
    if (rank === 3) return '🥉'
    return `#${rank}`
  }

  const getRankColor = (rank: number) => {
    if (rank === 1) return 'text-yellow-600 font-bold'
    if (rank === 2) return 'text-gray-500 font-bold'
    if (rank === 3) return 'text-orange-600 font-bold'
    return 'text-gray-700'
  }

  const totalBasePoints = entry.daily_scores.reduce((sum, score) => sum + score.base_points, 0)
  const totalBonusPoints = entry.daily_scores.reduce((sum, score) => sum + score.bonus_points, 0)

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className={`text-lg ${getRankColor(rank)}`}>
          {getRankBadge(rank)}
        </div>
      </td>
      <td className="px-6 py-4">
        <div className="font-medium text-gray-900">
          {entry.entry.participant?.name || 'Unknown'}
        </div>
        {entry.entry.weekend_bonus_forfeited && (
          <div className="text-xs text-orange-600 mt-1">
            Weekend bonus forfeited
          </div>
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right">
        <div className="text-lg font-semibold text-gray-900">
          {entry.total_points.toFixed(1)}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right text-gray-600">
        {totalBasePoints.toFixed(1)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right text-gray-600">
        {totalBonusPoints.toFixed(1)}
      </td>
    </tr>
  )
}
