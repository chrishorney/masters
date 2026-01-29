/** Leaderboard page */
import { useCurrentTournament, useLeaderboard, useCalculateScores } from '../hooks/useTournament'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { UpdateIndicator } from '../components/UpdateIndicator'
import { DiscordInvite } from '../components/DiscordInvite'
import type { LeaderboardEntry } from '../types'

export function LeaderboardPage() {
  const { data: tournament, isLoading: tournamentLoading } = useCurrentTournament()
  const { 
    data: leaderboardData, 
    isLoading: leaderboardLoading, 
    error: leaderboardError,
    refetch,
    isRefetching
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
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Leaderboard
          </h1>
          <p className="text-gray-600 text-sm md:text-base">
            {tournamentInfo.name} • Round {tournamentInfo.current_round}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
          <DiscordInvite />
          <button
            onClick={handleCalculateScores}
            disabled={calculateScores.isPending}
            className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm md:text-base"
          >
            {calculateScores.isPending ? 'Calculating...' : 'Recalculate Scores'}
          </button>
        </div>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-3">
        {entries.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-500">
            No entries found. Scores may need to be calculated.
          </div>
        ) : (
          entries.map((entry: LeaderboardEntry, index: number) => (
            <LeaderboardCard key={entry.entry.id} entry={entry} rank={index + 1} />
          ))
        )}
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block bg-white rounded-lg shadow-md overflow-hidden">
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
      <div className="mt-4 flex justify-center">
        <UpdateIndicator 
          lastUpdated={leaderboardData.last_updated}
          isRefetching={isRefetching}
        />
      </div>
    </div>
  )
}

function LeaderboardRow({ entry, rank }: { entry: LeaderboardEntry; rank: number }) {
  const navigate = (entryId: number) => {
    window.location.href = `/entry/${entryId}`
  }
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
    <tr 
      className="hover:bg-gray-50 transition-all duration-300 ease-in-out cursor-pointer"
      onClick={() => navigate(entry.entry.id)}
    >
      <td className="px-6 py-4 whitespace-nowrap">
        <div className={`text-lg ${getRankColor(rank)}`}>
          {getRankBadge(rank)}
        </div>
      </td>
      <td className="px-6 py-4">
        <div className="font-medium text-gray-900 hover:text-green-600 transition-colors">
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

function LeaderboardCard({ entry, rank }: { entry: LeaderboardEntry; rank: number }) {
  const navigate = (entryId: number) => {
    window.location.href = `/entry/${entryId}`
  }
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
    <div 
      className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-all cursor-pointer border-l-4 border-green-500"
      onClick={() => navigate(entry.entry.id)}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`text-2xl ${getRankColor(rank)}`}>
            {getRankBadge(rank)}
          </div>
          <div>
            <div className="font-semibold text-gray-900">
              {entry.entry.participant?.name || 'Unknown'}
            </div>
            {entry.entry.weekend_bonus_forfeited && (
              <div className="text-xs text-orange-600 mt-1">
                Weekend bonus forfeited
              </div>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">
            {entry.total_points.toFixed(1)}
          </div>
          <div className="text-xs text-gray-500">Total Points</div>
        </div>
      </div>
      <div className="flex justify-between text-sm text-gray-600 pt-3 border-t border-gray-100">
        <div>
          <span className="font-medium">Base:</span> {totalBasePoints.toFixed(1)}
        </div>
        <div>
          <span className="font-medium">Bonus:</span> {totalBonusPoints.toFixed(1)}
        </div>
      </div>
    </div>
  )
}
