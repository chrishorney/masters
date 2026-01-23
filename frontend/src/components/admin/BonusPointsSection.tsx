/** Manual bonus points management section */
import { useState, useEffect } from 'react'
import { adminApi } from '../../services/api'
import api from '../../services/api'

interface BonusPointsSectionProps {
  tournamentId: number
}

interface BonusPoint {
  id: number
  entry_id: number
  round_id: number
  bonus_type: string
  points: number
  player_id: string
  awarded_at: string
}

export function BonusPointsSection({ tournamentId }: BonusPointsSectionProps) {
  const [roundId, setRoundId] = useState<number>(1)
  const [playerSearch, setPlayerSearch] = useState('')
  const [bonusType, setBonusType] = useState<'gir_leader' | 'fairways_leader'>('gir_leader')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [selectedPlayer, setSelectedPlayer] = useState<any>(null)
  const [adding, setAdding] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  
  // Bonus points list state
  const [bonusPointsList, setBonusPointsList] = useState<BonusPoint[]>([])
  const [filterRound, setFilterRound] = useState<number | null>(null)
  const [loadingBonusPoints, setLoadingBonusPoints] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [playerMap, setPlayerMap] = useState<Record<string, string>>({})

  const handleSearch = async () => {
    if (!playerSearch.trim()) return

    try {
      const result = await adminApi.searchPlayers(playerSearch, tournamentId)
      setSearchResults(result.players)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to search players' })
    }
  }

  // Load bonus points list
  const loadBonusPoints = async () => {
    if (!tournamentId) {
      console.warn('BonusPointsSection: No tournamentId provided')
      return
    }
    
    setLoadingBonusPoints(true)
    try {
      console.log('Loading bonus points for tournament:', tournamentId, 'round:', filterRound)
      const result = await adminApi.listBonusPoints(tournamentId, filterRound || undefined)
      console.log('Bonus points result:', result)
      setBonusPointsList(result.bonus_points || [])
      
      // Get unique player IDs and fetch their names
      const uniquePlayerIds = [...new Set((result.bonus_points || []).map((bp: BonusPoint) => bp.player_id))]
      if (uniquePlayerIds.length > 0) {
        try {
          const tournamentPlayers = await adminApi.getTournamentPlayers(tournamentId)
          const playerNameMap: Record<string, string> = {}
          tournamentPlayers.players.forEach((p: any) => {
            playerNameMap[p.player_id] = p.full_name
          })
          setPlayerMap(playerNameMap)
        } catch (err) {
          console.error('Failed to load player names:', err)
        }
      }
    } catch (error: any) {
      console.error('Error loading bonus points:', error)
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to load bonus points' 
      })
    } finally {
      setLoadingBonusPoints(false)
    }
  }

  // Load bonus points on mount and when filter changes
  useEffect(() => {
    loadBonusPoints()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tournamentId, filterRound])

  const handleAddBonus = async () => {
    if (!selectedPlayer) {
      setMessage({ type: 'error', text: 'Please select a player' })
      return
    }

    setAdding(true)
    setMessage(null)

    try {
      const response = await api.post('/admin/bonus-points/add', {
        tournament_id: tournamentId,
        round_id: roundId,
        player_id: selectedPlayer.player_id,
        bonus_type: bonusType,
        points: 1.0,
      })

      setMessage({ 
        type: 'success', 
        text: `Bonus added! ${response.data.bonus_points_created || 0} bonus points created.` 
      })
      setSelectedPlayer(null)
      setPlayerSearch('')
      setSearchResults([])
      // Reload bonus points list
      await loadBonusPoints()
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to add bonus point' 
      })
    } finally {
      setAdding(false)
    }
  }

  const getBonusTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'gir_leader': 'GIR Leader',
      'fairways_leader': 'Fairways Leader',
    }
    return labels[type] || type
  }

  // Group bonus points by round
  const groupedByRound = bonusPointsList.reduce((acc, bp) => {
    if (!acc[bp.round_id]) {
      acc[bp.round_id] = []
    }
    acc[bp.round_id].push(bp)
    return acc
  }, {} as Record<number, BonusPoint[]>)

  const rounds = Object.keys(groupedByRound).map(Number).sort()

  return (
    <div className="space-y-6">
      {/* Add Bonus Point */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-4">Add Manual Bonus Point</h2>
        
        <div className="space-y-4">
          {/* Round Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Round
            </label>
            <select
              value={roundId}
              onChange={(e) => setRoundId(parseInt(e.target.value))}
              className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
            >
              <option value={1}>Round 1</option>
              <option value={2}>Round 2</option>
              <option value={3}>Round 3</option>
              <option value={4}>Round 4</option>
            </select>
          </div>

          {/* Bonus Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bonus Type
            </label>
            <select
              value={bonusType}
              onChange={(e) => setBonusType(e.target.value as 'gir_leader' | 'fairways_leader')}
              className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
            >
              <option value="gir_leader">GIR Leader</option>
              <option value="fairways_leader">Fairways Leader</option>
            </select>
          </div>

          {/* Player Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Player
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={playerSearch}
                onChange={(e) => setPlayerSearch(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Enter player name..."
                className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
              />
              <button
                onClick={handleSearch}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Search
              </button>
            </div>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Player
              </label>
              <div className="max-h-48 overflow-y-auto border border-gray-300 rounded-lg">
                {searchResults.map((player) => (
                  <button
                    key={player.player_id}
                    onClick={() => setSelectedPlayer(player)}
                    className={`w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors ${
                      selectedPlayer?.player_id === player.player_id ? 'bg-green-50 border-l-4 border-green-500' : ''
                    }`}
                  >
                    <div className="font-medium text-gray-900">{player.full_name}</div>
                    <div className="text-sm text-gray-500">ID: {player.player_id}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Selected Player */}
          {selectedPlayer && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="font-medium text-green-900">Selected: {selectedPlayer.full_name}</div>
              <div className="text-sm text-green-700">ID: {selectedPlayer.player_id}</div>
            </div>
          )}

          {/* Add Button */}
          <button
            onClick={handleAddBonus}
            disabled={!selectedPlayer || adding}
            className="w-full px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {adding ? 'Adding...' : 'Add Bonus Point'}
          </button>
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

      {/* Existing Bonus Points List */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4 gap-4">
          <h2 className="text-xl md:text-2xl font-semibold text-gray-900">Assigned Bonus Points</h2>
          
          {/* Filter by Round */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Filter by Round:</label>
            <select
              value={filterRound || ''}
              onChange={(e) => setFilterRound(e.target.value ? parseInt(e.target.value) : null)}
              className="px-3 py-1 rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 text-sm"
            >
              <option value="">All Rounds</option>
              <option value="1">Round 1</option>
              <option value="2">Round 2</option>
              <option value="3">Round 3</option>
              <option value="4">Round 4</option>
            </select>
            <button
              onClick={loadBonusPoints}
              disabled={loadingBonusPoints}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              {loadingBonusPoints ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>

        {loadingBonusPoints ? (
          <div className="text-center py-8 text-gray-500">Loading bonus points...</div>
        ) : bonusPointsList.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No bonus points assigned yet.
          </div>
        ) : (
          <div className="space-y-6">
            {rounds.map((round) => {
              const roundBonusPoints = groupedByRound[round]
              // Group by player_id and bonus_type to show unique assignments
              const uniqueAssignments = roundBonusPoints.reduce((acc, bp) => {
                const key = `${bp.player_id}-${bp.bonus_type}`
                if (!acc[key]) {
                  acc[key] = {
                    player_id: bp.player_id,
                    bonus_type: bp.bonus_type,
                    points: bp.points,
                    count: 0,
                    ids: [] as number[]
                  }
                }
                acc[key].count++
                acc[key].ids.push(bp.id)
                return acc
              }, {} as Record<string, { player_id: string; bonus_type: string; points: number; count: number; ids: number[] }>)

              return (
                <div key={round} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Round {round}</h3>
                  <div className="space-y-2">
                    {Object.values(uniqueAssignments).map((assignment) => (
                      <div
                        key={`${assignment.player_id}-${assignment.bonus_type}`}
                        className="flex flex-col md:flex-row md:items-center md:justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors gap-2"
                      >
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">
                            {getBonusTypeLabel(assignment.bonus_type)}
                          </div>
                          <div className="text-sm text-gray-600">
                            Player: {playerMap[assignment.player_id] || `ID: ${assignment.player_id}`}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            Applied to {assignment.count} {assignment.count === 1 ? 'entry' : 'entries'} • {assignment.points} {assignment.points === 1 ? 'point' : 'points'} each
                          </div>
                        </div>
                        <button
                          onClick={async () => {
                            // Delete all bonus points for this player/type/round combination
                            if (confirm(`Delete all ${assignment.count} bonus point(s) for ${getBonusTypeLabel(assignment.bonus_type)}? This will remove the bonus from all ${assignment.count} entries and recalculate their scores.`)) {
                              setDeletingId(assignment.ids[0]) // Use first ID for loading state
                              try {
                                // Delete all IDs sequentially to avoid overwhelming the server
                                for (const id of assignment.ids) {
                                  await adminApi.deleteBonusPoint(id)
                                }
                                setMessage({ 
                                  type: 'success', 
                                  text: `Deleted ${assignment.count} bonus point(s). Scores have been recalculated.` 
                                })
                                await loadBonusPoints()
                              } catch (error: any) {
                                setMessage({ 
                                  type: 'error', 
                                  text: error.response?.data?.detail || 'Failed to delete bonus points' 
                                })
                              } finally {
                                setDeletingId(null)
                              }
                            }
                          }}
                          disabled={deletingId !== null}
                          className="w-full md:w-auto px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {deletingId !== null && assignment.ids.includes(deletingId) ? 'Deleting...' : 'Delete All'}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">About Manual Bonus Points</h4>
        <div className="text-sm text-blue-800 space-y-1">
          <p>• GIR (Greens in Regulation) and Fairways Hit leaders are not available in the API</p>
          <p>• These must be added manually after each round</p>
          <p>• The bonus will automatically be applied to all entries that have the selected player</p>
          <p>• Scores will be automatically recalculated after adding or deleting a bonus</p>
          <p>• Use the "Assigned Bonus Points" section above to view and manage existing bonuses</p>
        </div>
      </div>
    </div>
  )
}
