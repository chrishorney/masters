/** Tournament Leaderboard page with round snapshots - shows actual golfers */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useCurrentTournament } from '../hooks/useTournament'
import { scoresApi } from '../services/api'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { UpdateIndicator } from '../components/UpdateIndicator'
import { formatCentralTime } from '../utils/time'
import type { TournamentLeaderboardPlayer } from '../types'

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
        return await scoresApi.getTournamentLeaderboard(tournament.id)
      } else {
        return await scoresApi.getRoundTournamentLeaderboard(tournament.id, selectedView)
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

  const { leaderboard, tournament: tournamentInfo, view_type, round_id, snapshot_timestamp } = leaderboardData
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

      {/* Leaderboard Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-green-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Position
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Player
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {leaderboard.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-6 py-8 text-center text-gray-500">
                    No leaderboard data available. Please sync tournament data.
                  </td>
                </tr>
              ) : (
                leaderboard.map((player: TournamentLeaderboardPlayer, index: number) => (
                  <LeaderboardRow key={`${player.player_id}-${index}`} player={player} />
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

function LeaderboardRow({ player }: { player: TournamentLeaderboardPlayer }) {
  const getPositionDisplay = (position: string) => {
    // Position might be "1", "T2", "T3", etc.
    if (!position) return '-'
    return position
  }

  const getScoreDisplay = (score: string) => {
    if (!score) return '-'
    // Score is already formatted (e.g., "-5", "E", "+2")
    return score
  }

  const isCut = player.status === 'cut'
  const isWithdrawn = player.status === 'wd'
  const isDisqualified = player.status === 'dq'

  return (
    <tr className={`hover:bg-gray-50 transition-colors ${isCut || isWithdrawn || isDisqualified ? 'opacity-60' : ''}`}>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm font-medium text-gray-900">
          {getPositionDisplay(player.position)}
        </div>
      </td>
      <td className="px-6 py-4">
        <div className="text-sm font-medium text-gray-900">
          {player.player_name}
        </div>
        {(isCut || isWithdrawn || isDisqualified) && (
          <div className="text-xs text-gray-500 mt-1">
            {isCut && 'Cut'}
            {isWithdrawn && 'WD'}
            {isDisqualified && 'DQ'}
          </div>
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right">
        <div className={`text-sm font-semibold ${
          getScoreDisplay(player.score).startsWith('-') 
            ? 'text-green-600' 
            : getScoreDisplay(player.score).startsWith('+') 
            ? 'text-red-600' 
            : 'text-gray-900'
        }`}>
          {getScoreDisplay(player.score)}
        </div>
      </td>
    </tr>
  )
}
