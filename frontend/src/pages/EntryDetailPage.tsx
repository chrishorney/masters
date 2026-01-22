/** Entry detail page showing individual entry breakdown */
import { useParams, Link } from 'react-router-dom'
import { useEntryDetails } from '../hooks/useEntry'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'

export function EntryDetailPage() {
  const { entryId } = useParams<{ entryId: string }>()
  const entryIdNum = entryId ? parseInt(entryId, 10) : undefined
  
  const { data: entryData, isLoading, error } = useEntryDetails(entryIdNum)

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error || !entryData) {
    return (
      <div className="max-w-4xl mx-auto">
        <ErrorMessage 
          message="Failed to load entry details. Please try again later."
          onRetry={() => window.location.reload()}
        />
        <div className="mt-4">
          <Link to="/leaderboard" className="text-green-600 hover:text-green-700 underline">
            ← Back to Leaderboard
          </Link>
        </div>
      </div>
    )
  }

  const { entry, tournament, players, rebuy_players, daily_scores, bonus_points, totals } = entryData

  const getPlayerName = (playerId: string) => {
    return players[playerId]?.full_name || `Player ${playerId}`
  }

  const getRebuyPlayerName = (playerId: string) => {
    return rebuy_players[playerId]?.full_name || `Player ${playerId}`
  }

  const getBonusTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'gir_leader': 'GIR Leader',
      'fairways_leader': 'Fairways Leader',
      'low_score': 'Low Score of Day',
      'eagle': 'Eagle',
      'double_eagle': 'Double Eagle',
      'hole_in_one': 'Hole-in-One',
      'all_make_cut': 'All 6 Make Cut',
    }
    return labels[type] || type
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link to="/leaderboard" className="text-green-600 hover:text-green-700 underline mb-4 inline-block">
          ← Back to Leaderboard
        </Link>
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          {entry.participant.name}'s Entry
        </h1>
        {tournament && (
          <p className="text-gray-600">
            {tournament.name} • Round {tournament.current_round}
          </p>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-500 mb-1">Total Points</div>
          <div className="text-3xl font-bold text-gray-900">{totals.total_points.toFixed(1)}</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-500 mb-1">Base Points</div>
          <div className="text-3xl font-bold text-gray-700">{totals.total_base_points.toFixed(1)}</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-500 mb-1">Bonus Points</div>
          <div className="text-3xl font-bold text-green-600">{totals.total_bonus_points.toFixed(1)}</div>
        </div>
      </div>

      {/* Selected Players */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Selected Players</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            entry.player1_id,
            entry.player2_id,
            entry.player3_id,
            entry.player4_id,
            entry.player5_id,
            entry.player6_id,
          ].map((playerId, index) => {
            const isRebuy = entry.rebuy_original_player_ids?.includes(playerId)
            const rebuyInfo = isRebuy 
              ? entry.rebuy_player_ids?.[entry.rebuy_original_player_ids.indexOf(playerId)]
              : null
            
            return (
              <div key={playerId} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-gray-900">
                      Player {index + 1}: {getPlayerName(playerId)}
                    </div>
                    {isRebuy && rebuyInfo && (
                      <div className="text-sm text-orange-600 mt-1">
                        Rebuy: {getRebuyPlayerName(rebuyInfo)} ({entry.rebuy_type})
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
        
        {entry.weekend_bonus_earned && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <span className="text-green-800 font-medium">✓ Weekend Bonus Earned (All 6 Made Cut)</span>
          </div>
        )}
        
        {entry.weekend_bonus_forfeited && (
          <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
            <span className="text-orange-800 font-medium">⚠ Weekend Bonus Forfeited (Underperformer Rebuy)</span>
          </div>
        )}
      </div>

      {/* Daily Scores */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Round-by-Round Scores</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Round</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Base Points</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Bonus Points</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {daily_scores.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                    No scores calculated yet
                  </td>
                </tr>
              ) : (
                daily_scores.map((score: any) => (
                  <tr key={score.round_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">Round {score.round_id}</td>
                    <td className="px-4 py-3 text-right text-gray-700">{score.base_points.toFixed(1)}</td>
                    <td className="px-4 py-3 text-right text-green-600">{score.bonus_points.toFixed(1)}</td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">{score.total_points.toFixed(1)}</td>
                  </tr>
                ))
              )}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr>
                <td className="px-4 py-3 font-bold text-gray-900">Total</td>
                <td className="px-4 py-3 text-right font-bold text-gray-900">{totals.total_base_points.toFixed(1)}</td>
                <td className="px-4 py-3 text-right font-bold text-green-600">{totals.total_bonus_points.toFixed(1)}</td>
                <td className="px-4 py-3 text-right font-bold text-gray-900">{totals.total_points.toFixed(1)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Bonus Points Breakdown */}
      {bonus_points.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Bonus Points Breakdown</h2>
          <div className="space-y-2">
            {bonus_points.map((bp: any) => (
              <div key={bp.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900">{getBonusTypeLabel(bp.bonus_type)}</span>
                  {bp.player_id && (
                    <span className="text-gray-600 ml-2">
                      ({players[bp.player_id]?.full_name || `Player ${bp.player_id}`})
                    </span>
                  )}
                  <span className="text-sm text-gray-500 ml-2">Round {bp.round_id}</span>
                </div>
                <div className="font-semibold text-green-600">+{bp.points.toFixed(1)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
