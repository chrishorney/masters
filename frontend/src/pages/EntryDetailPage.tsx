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
        <Link to="/leaderboard" className="text-green-600 hover:text-green-700 underline mb-4 inline-block text-sm md:text-base">
          ← Back to Leaderboard
        </Link>
        <h1 className="text-2xl md:text-4xl font-bold text-gray-900 mb-2">
          {entry.participant.name}'s Entry
        </h1>
        {tournament && (
          <p className="text-gray-600 text-sm md:text-base">
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
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-8">
        <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-4">Selected Players</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

      {/* Daily Scores Summary */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-8">
        <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-4">Round-by-Round Scores</h2>
        <div className="overflow-x-auto -mx-4 md:mx-0">
          <div className="inline-block min-w-full px-4 md:px-0">
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
                    <td className="px-4 py-3 font-medium text-gray-900">
                      Round {score.round_id}
                      {tournament && score.round_id === tournament.current_round && (
                        <span className="ml-2 text-xs text-green-600 font-semibold">(Current)</span>
                      )}
                    </td>
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
      </div>

      {/* Per-Player Points Per Round */}
      {daily_scores.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-8">
          <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-4">Player Points Per Round</h2>
          <div className="space-y-6">
            {daily_scores.map((score: any) => {
              const baseBreakdown = score.details?.base_breakdown || {}
              const roundBonuses = bonus_points.filter((bp: any) => bp.round_id === score.round_id)
              
              // Determine which players were active this round
              // Rounds 1-2: Always use original 6 players
              // Rounds 3-4: Use rebuy players if they exist, otherwise original players
              const originalPlayerIds = [
                entry.player1_id,
                entry.player2_id,
                entry.player3_id,
                entry.player4_id,
                entry.player5_id,
                entry.player6_id,
              ]
              
              const isRebuyRound = score.round_id >= 3
              let activePlayerIds: string[] = originalPlayerIds
              
              if (isRebuyRound && entry.rebuy_player_ids && entry.rebuy_player_ids.length > 0) {
                // Create mapping: for each original player position, use rebuy if it exists
                activePlayerIds = originalPlayerIds.map((origId, index) => {
                  const rebuyIndex = entry.rebuy_original_player_ids?.indexOf(origId)
                  if (rebuyIndex !== undefined && rebuyIndex >= 0 && entry.rebuy_player_ids?.[rebuyIndex]) {
                    return entry.rebuy_player_ids[rebuyIndex]
                  }
                  return origId
                })
              }
              
              // Calculate player totals for this round (base + bonus)
              const playerRoundTotals: Record<string, number> = {}
              
              // Add base points
              Object.keys(baseBreakdown).forEach((playerKey) => {
                const playerData = baseBreakdown[playerKey]
                const playerId = playerData.player_id
                if (playerId) {
                  playerRoundTotals[playerId] = (playerRoundTotals[playerId] || 0) + (playerData.points || 0)
                }
              })
              
              // Add bonus points
              roundBonuses.forEach((bp: any) => {
                if (bp.player_id) {
                  playerRoundTotals[bp.player_id] = (playerRoundTotals[bp.player_id] || 0) + (bp.points || 0)
                }
              })
              
              return (
                <div key={score.round_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Round {score.round_id}
                      {tournament && score.round_id === tournament.current_round && (
                        <span className="ml-2 text-sm text-green-600 font-semibold">(Current)</span>
                      )}
                    </h3>
                    <div className="text-sm text-gray-500">
                      Total: <span className="font-semibold text-gray-900">{score.total_points.toFixed(1)} pts</span>
                    </div>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Player</th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Position</th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Base Points</th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Bonus Points</th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Round Total</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {activePlayerIds.map((playerId: string, index: number) => {
                          const playerData = baseBreakdown[`player${index + 1}`] || {}
                          const playerBonuses = roundBonuses.filter((bp: any) => bp.player_id === playerId)
                          const playerBonusTotal = playerBonuses.reduce((sum: number, bp: any) => sum + bp.points, 0)
                          const playerBasePoints = playerData.points || 0
                          const playerRoundTotal = playerBasePoints + playerBonusTotal
                          
                          // Check if this is a rebuy player (playerId is in rebuy list but not in original list)
                          const isRebuy = isRebuyRound && 
                            entry.rebuy_player_ids?.includes(playerId) && 
                            !originalPlayerIds.includes(playerId)
                          const originalPlayerId = isRebuy 
                            ? entry.rebuy_original_player_ids?.[entry.rebuy_player_ids.indexOf(playerId)]
                            : null
                          
                          return (
                            <tr key={playerId} className="hover:bg-gray-50">
                              <td className="px-3 py-2">
                                <div className="font-medium text-gray-900">
                                  {players[playerId]?.full_name || rebuy_players[playerId]?.full_name || `Player ${playerId}`}
                                </div>
                                {isRebuy && originalPlayerId && (
                                  <div className="text-xs text-orange-600 mt-1">
                                    Rebuy (was {players[originalPlayerId]?.full_name || `Player ${originalPlayerId}`})
                                  </div>
                                )}
                              </td>
                              <td className="px-3 py-2 text-right text-gray-600">
                                {playerData.position || '-'}
                              </td>
                              <td className="px-3 py-2 text-right text-gray-700">
                                {playerBasePoints.toFixed(1)}
                              </td>
                              <td className="px-3 py-2 text-right text-green-600">
                                {playerBonusTotal > 0 ? `+${playerBonusTotal.toFixed(1)}` : '0.0'}
                                {playerBonuses.length > 0 && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    {playerBonuses.map((bp: any) => getBonusTypeLabel(bp.bonus_type)).join(', ')}
                                  </div>
                                )}
                              </td>
                              <td className="px-3 py-2 text-right font-semibold text-gray-900">
                                {playerRoundTotal.toFixed(1)}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                      <tfoot className="bg-gray-50">
                        <tr>
                          <td colSpan={2} className="px-3 py-2 font-bold text-gray-900">Round Total</td>
                          <td className="px-3 py-2 text-right font-bold text-gray-900">{score.base_points.toFixed(1)}</td>
                          <td className="px-3 py-2 text-right font-bold text-green-600">{score.bonus_points.toFixed(1)}</td>
                          <td className="px-3 py-2 text-right font-bold text-gray-900">{score.total_points.toFixed(1)}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Player Totals Across All Rounds */}
      {daily_scores.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-8">
          <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-4">Player Totals (All Rounds)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Player</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Rounds Played</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total Base Points</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total Bonus Points</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total Points</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {(() => {
                  // Aggregate points per player across all rounds
                  const playerTotals: Record<string, {
                    name: string
                    basePoints: number
                    bonusPoints: number
                    rounds: Set<number>
                    isRebuy: boolean
                    originalPlayerId?: string
                  }> = {}
                  
                  // Get all unique player IDs (original + rebuy)
                  const allPlayerIds = new Set<string>()
                  const originalPlayerIds = [
                    entry.player1_id,
                    entry.player2_id,
                    entry.player3_id,
                    entry.player4_id,
                    entry.player5_id,
                    entry.player6_id,
                  ]
                  originalPlayerIds.forEach(id => allPlayerIds.add(id))
                  if (entry.rebuy_player_ids) {
                    entry.rebuy_player_ids.forEach(id => allPlayerIds.add(id))
                  }
                  
                  // Initialize player totals
                  allPlayerIds.forEach(playerId => {
                    const player = players[playerId] || rebuy_players[playerId]
                    // Check if this is a rebuy player (in rebuy list but not in original)
                    const isRebuy = entry.rebuy_player_ids?.includes(playerId) && 
                                    !originalPlayerIds.includes(playerId)
                    const originalPlayerId = isRebuy 
                      ? entry.rebuy_original_player_ids?.[entry.rebuy_player_ids.indexOf(playerId)]
                      : null
                    
                    playerTotals[playerId] = {
                      name: player?.full_name || `Player ${playerId}`,
                      basePoints: 0,
                      bonusPoints: 0,
                      rounds: new Set(),
                      isRebuy: !!isRebuy,
                      originalPlayerId: originalPlayerId || undefined,
                    }
                  })
                  
                  // Aggregate from daily scores
                  daily_scores.forEach((score: any) => {
                    const baseBreakdown = score.details?.base_breakdown || {}
                    const roundBonuses = bonus_points.filter((bp: any) => bp.round_id === score.round_id)
                    
                    // Add base points
                    Object.keys(baseBreakdown).forEach((playerKey) => {
                      const playerData = baseBreakdown[playerKey]
                      const playerId = playerData.player_id
                      if (playerId && playerTotals[playerId]) {
                        playerTotals[playerId].basePoints += playerData.points || 0
                        playerTotals[playerId].rounds.add(score.round_id)
                      }
                    })
                    
                    // Add bonus points
                    roundBonuses.forEach((bp: any) => {
                      if (bp.player_id && playerTotals[bp.player_id]) {
                        playerTotals[bp.player_id].bonusPoints += bp.points || 0
                        playerTotals[bp.player_id].rounds.add(score.round_id)
                      }
                    })
                  })
                  
                  // Sort by total points descending
                  const sortedPlayers = Object.entries(playerTotals)
                    .map(([playerId, totals]) => ({
                      playerId,
                      ...totals,
                      totalPoints: totals.basePoints + totals.bonusPoints,
                    }))
                    .sort((a, b) => b.totalPoints - a.totalPoints)
                  
                  return sortedPlayers.map(({ playerId, name, basePoints, bonusPoints, rounds, isRebuy, originalPlayerId, totalPoints }) => (
                    <tr key={playerId} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{name}</div>
                        {isRebuy && originalPlayerId && (
                          <div className="text-xs text-orange-600 mt-1">
                            Rebuy (was {players[originalPlayerId]?.full_name || `Player ${originalPlayerId}`})
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">
                        {Array.from(rounds).sort().join(', ')}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700">{basePoints.toFixed(1)}</td>
                      <td className="px-4 py-3 text-right text-green-600">{bonusPoints.toFixed(1)}</td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-900">{totalPoints.toFixed(1)}</td>
                    </tr>
                  ))
                })()}
              </tbody>
              <tfoot className="bg-gray-50">
                <tr>
                  <td className="px-4 py-3 font-bold text-gray-900">Total</td>
                  <td className="px-4 py-3 text-right font-bold text-gray-900">-</td>
                  <td className="px-4 py-3 text-right font-bold text-gray-900">{totals.total_base_points.toFixed(1)}</td>
                  <td className="px-4 py-3 text-right font-bold text-green-600">{totals.total_bonus_points.toFixed(1)}</td>
                  <td className="px-4 py-3 text-right font-bold text-gray-900">{totals.total_points.toFixed(1)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Bonus Points Breakdown */}
      {bonus_points.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
          <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-4">Bonus Points Breakdown</h2>
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
