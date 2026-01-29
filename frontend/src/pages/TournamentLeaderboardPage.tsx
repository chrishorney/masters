/** Tournament Leaderboard page with round snapshots */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useCurrentTournament } from '../hooks/useTournament'
import { scoresApi } from '../services/api'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { UpdateIndicator } from '../components/UpdateIndicator'
import { formatCentralTime } from '../utils/time'
import type { LeaderboardEntry } from '../types'

export function TournamentLeaderboardPage() {
  const { data: tournament, isLoading: tournamentLoading } = useCurrentTournament()
  const [selectedView, setSelectedView] = useState<'current' | number>('current')

  // Determine available rounds (1 through current_round)
  const availableRounds = tournament
    ? Array.from({ length: tournament.current_round }, (_, i) => i + 1)
    : []

  // Fetch leaderboard data based on selection
  const {
    data: leaderboardData,
    isLoading: leaderboardLoading,
    error: leaderboardError,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['tournament-leaderboard', tournament?.id, selectedView],
    queryFn: async () => {
      if (!tournament) throw new Error('No tournament')
      
      if (selectedView === 'current') {
        return await scoresApi.getLeaderboard(tournament.id)
      } else {
        return await scoresApi.getRoundLeaderboard(tournament.id, selectedView)
      }
    },
    enabled: !!tournament,
    refetchInterval: selectedView === 'current' ? 60000 : false, // Auto-refresh current view every minute
    staleTime: selectedView === 'current' ? 30000 : Infinity, // Current view is stale after 30s, snapshots never stale
  })

  if (tournamentLoading || leaderboardLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (leaderboardError || !leaderboardData || !tournament) {
    return (
      <div className="max-w-4xl mx-auto">
        <ErrorMessage
          message="Failed to load leaderboard. Please try again later."
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  const { entries, tournament: tournamentInfo, view_type, round_id, snapshot_timestamp } = leaderboardData
  const isSnapshot = view_type === 'round_snapshot'

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Tournament Leaderboard
          </h1>
          <p className="text-gray-600 text-sm md:text-base">
            {tournamentInfo.name}
            {isSnapshot && ` • Round ${round_id} Snapshot`}
            {!isSnapshot && ` • Round ${tournamentInfo.current_round} (Live)`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label htmlFor="round-select" className="text-sm font-medium text-gray-700">
            View:
          </label>
          <select
            id="round-select"
            value={selectedView === 'current' ? 'current' : selectedView}
            onChange={(e) => {
              const value = e.target.value
              setSelectedView(value === 'current' ? 'current' : parseInt(value, 10))
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white text-gray-900"
          >
            <option value="current">Current (Live)</option>
            {availableRounds.map((round) => (
              <option key={round} value={round}>
                Round {round} Snapshot
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Snapshot Info Banner */}
      {isSnapshot && snapshot_timestamp && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-sm text-blue-800">
              <strong>Round {round_id} Snapshot:</strong> This leaderboard shows standings as of{' '}
              {formatCentralTime(snapshot_timestamp)} CT. This is a static snapshot and will not update.
            </p>
          </div>
        </div>
      )}

      {/* Mobile Card View */}
      <div className="md:hidden space-y-3">
        {entries.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-500">
            No entries found.
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
                    No entries found.
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
      {!isSnapshot && (
        <div className="mt-4 flex justify-center">
          <UpdateIndicator
            lastUpdated={leaderboardData.last_updated}
            isRefetching={isRefetching}
          />
        </div>
      )}
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
