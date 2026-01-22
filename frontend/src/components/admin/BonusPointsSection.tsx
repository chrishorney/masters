/** Manual bonus points management section */
import { useState } from 'react'
import { adminApi } from '../../services/api'
import api from '../../services/api'

interface BonusPointsSectionProps {
  tournamentId: number
}

export function BonusPointsSection({ tournamentId }: BonusPointsSectionProps) {
  const [roundId, setRoundId] = useState<number>(1)
  const [playerSearch, setPlayerSearch] = useState('')
  const [bonusType, setBonusType] = useState<'gir_leader' | 'fairways_leader'>('gir_leader')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [selectedPlayer, setSelectedPlayer] = useState<any>(null)
  const [adding, setAdding] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleSearch = async () => {
    if (!playerSearch.trim()) return

    try {
      const result = await adminApi.searchPlayers(playerSearch, tournamentId)
      setSearchResults(result.players)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to search players' })
    }
  }

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
        text: `Bonus added! ${response.data.entries_updated || 0} entries updated.` 
      })
      setSelectedPlayer(null)
      setPlayerSearch('')
      setSearchResults([])
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to add bonus point' 
      })
    } finally {
      setAdding(false)
    }
  }

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

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">About Manual Bonus Points</h4>
        <div className="text-sm text-blue-800 space-y-1">
          <p>• GIR (Greens in Regulation) and Fairways Hit leaders are not available in the API</p>
          <p>• These must be added manually after each round</p>
          <p>• The bonus will automatically be applied to all entries that have the selected player</p>
          <p>• Scores will be automatically recalculated after adding a bonus</p>
        </div>
      </div>
    </div>
  )
}
