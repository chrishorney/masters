/** Leaderboard page */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useCurrentTournament, useLeaderboard } from '../hooks/useTournament'
import { scoresApi } from '../services/api'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { UpdateIndicator } from '../components/UpdateIndicator'
import { DiscordInvite } from '../components/DiscordInvite'
import { DiscordWidget } from '../components/DiscordWidget'
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

  const [selectedPlayerId, setSelectedPlayerId] = useState<string>('')
  const { data: tournamentLeaderboard } = useQuery({
    queryKey: ['tournament-leaderboard', tournament?.id],
    queryFn: () => scoresApi.getTournamentLeaderboard(tournament!.id),
    enabled: !!tournament?.id,
    staleTime: 60 * 1000,
  })
  const { data: entriesByPlayer, isLoading: entriesByPlayerLoading } = useQuery({
    queryKey: ['entries-by-player', tournament?.id, selectedPlayerId],
    queryFn: () => scoresApi.getEntriesByPlayer(tournament!.id, selectedPlayerId),
    enabled: !!tournament?.id && !!selectedPlayerId,
  })
  const golfers = tournamentLeaderboard?.leaderboard ?? []
  const selectedPlayerName = selectedPlayerId
    ? (golfers.find((g) => g.player_id === selectedPlayerId)?.player_name ?? entriesByPlayer?.player_name ?? selectedPlayerId)
    : ''

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
        </div>
      </div>

      {/* Find entries by golfer */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow border border-gray-200">
        <label htmlFor="golfer-select" className="block text-sm font-medium text-gray-700 mb-2">
          Find entries with golfer
        </label>
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
          <select
            id="golfer-select"
            value={selectedPlayerId}
            onChange={(e) => setSelectedPlayerId(e.target.value)}
            className="block w-full sm:w-72 rounded-md border border-gray-300 bg-white py-2 pl-3 pr-10 text-base focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
          >
            <option value="">Select a golfer...</option>
            {golfers.map((g) => (
              <option key={g.player_id} value={g.player_id}>
                {g.player_name}
              </option>
            ))}
          </select>
          {selectedPlayerId && (
            <button
              type="button"
              onClick={() => setSelectedPlayerId('')}
              className="text-sm text-gray-500 hover:text-gray-700 underline"
            >
              Clear
            </button>
          )}
        </div>
        {selectedPlayerId && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            {entriesByPlayerLoading ? (
              <p className="text-sm text-gray-500">Loading...</p>
            ) : entriesByPlayer && entriesByPlayer.entries.length > 0 ? (
              <>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>{selectedPlayerName}</strong> is on {entriesByPlayer.entries.length} roster
                  {entriesByPlayer.entries.length !== 1 ? 's' : ''}:
                </p>
                <ul className="list-none space-y-1">
                  {entriesByPlayer.entries.map(({ entry_id, participant_name }) => (
                    <li key={entry_id}>
                      <Link
                        to={`/entry/${entry_id}`}
                        className="text-green-600 hover:text-green-800 hover:underline font-medium"
                      >
                        {participant_name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </>
            ) : entriesByPlayer ? (
              <p className="text-sm text-gray-500">No entries have this golfer on their roster.</p>
            ) : null}
          </div>
        )}
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

      {/* Discord Widget */}
      <div className="mt-8">
        <DiscordWidget />
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
