/** API client for backend communication */
import axios from 'axios'
import type {
  Tournament,
  LeaderboardResponse,
  Player,
} from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_PREFIX = '/api'

const api = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Tournament endpoints
export const tournamentApi = {
  /** Get current tournament */
  getCurrent: async (): Promise<Tournament> => {
    const response = await api.get('/tournament/current')
    return response.data
  },

  /** Get tournament by ID */
  getById: async (id: number): Promise<Tournament> => {
    const response = await api.get(`/tournament/${id}`)
    return response.data
  },

  /** Sync tournament data from API */
  sync: async (orgId?: string, tournId?: string, year?: number): Promise<{ success: boolean; message: string }> => {
    const params: any = {}
    if (orgId) params.org_id = orgId
    if (tournId) params.tourn_id = tournId
    if (year) params.year = year
    const response = await api.post('/tournament/sync', null, { params })
    return { success: true, message: response.data.message || 'Tournament synced' }
  },
}

// Scores endpoints
export const scoresApi = {
  /** Get leaderboard for tournament */
  getLeaderboard: async (tournamentId: number): Promise<LeaderboardResponse> => {
    const response = await api.get('/scores/leaderboard', {
      params: { tournament_id: tournamentId },
    })
    return response.data
  },

  /** Calculate scores for tournament */
  calculateScores: async (tournamentId: number, roundId?: number): Promise<{ success: boolean; message: string }> => {
    const params: any = { tournament_id: tournamentId }
    if (roundId) params.round_id = roundId
    const response = await api.post('/scores/calculate', null, { params })
    return { success: true, message: response.data.message || 'Scores calculated' }
  },
}

// Admin endpoints (for player search, etc.)
export const adminApi = {
  /** Search players by name */
  searchPlayers: async (name: string, tournamentId?: number): Promise<{ players: Player[] }> => {
    const params: any = { name }
    if (tournamentId) params.tournament_id = tournamentId
    const response = await api.get('/admin/players/search', { params })
    return response.data
  },

  /** Get tournament players */
  getTournamentPlayers: async (tournamentId: number): Promise<{ players: Player[] }> => {
    const response = await api.get(`/admin/players/tournament/${tournamentId}`)
    return response.data
  },

  /** Preview import (get tournament players) */
  previewImport: async (tournamentId: number, limit = 10): Promise<{ players: Player[] }> => {
    const response = await api.get('/admin/import/preview', {
      params: { tournament_id: tournamentId, limit },
    })
    return response.data
  },
}

export default api
