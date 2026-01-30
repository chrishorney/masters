/** API client for backend communication */
import axios from 'axios'
import type {
  Tournament,
  LeaderboardResponse,
  TournamentLeaderboardResponse,
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

// Public Discord endpoint
export const discordApi = {
  /** Get Discord invite URL (public) */
  getInviteUrl: async (): Promise<{ invite_url: string }> => {
    const response = await api.get('/discord/invite')
    return response.data
  },
  /** Get Discord widget info (public) */
  getWidgetInfo: async (): Promise<{ server_id: string; widget_url: string }> => {
    const response = await api.get('/discord/widget')
    return response.data
  },
}

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

  /** Get leaderboard snapshot for a specific round */
  getRoundLeaderboard: async (tournamentId: number, roundId: number): Promise<LeaderboardResponse> => {
    const response = await api.get(`/scores/leaderboard/round/${roundId}`, {
      params: { tournament_id: tournamentId },
    })
    return response.data
  },

  /** Get tournament leaderboard (golfers, not pool entries) */
  getTournamentLeaderboard: async (tournamentId: number): Promise<TournamentLeaderboardResponse> => {
    const response = await api.get('/scores/tournament-leaderboard', {
      params: { tournament_id: tournamentId },
    })
    return response.data
  },

  /** Get tournament leaderboard snapshot for a specific round */
  getRoundTournamentLeaderboard: async (tournamentId: number, roundId: number): Promise<TournamentLeaderboardResponse> => {
    const response = await api.get(`/scores/tournament-leaderboard/round/${roundId}`, {
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

// Entry endpoints
export const entryApi = {
  /** Get entry details */
  getEntryDetails: async (entryId: number): Promise<any> => {
    const response = await api.get(`/entry/${entryId}`)
    return response.data
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

  /** Start background job for automatic sync */
  startBackgroundJob: async (
    tournamentId: number, 
    intervalSeconds: number = 300,
    startHour: number = 6,
    stopHour: number = 23
  ): Promise<{ message: string; status: string; active_hours: string }> => {
    const response = await api.post('/admin/jobs/start', null, {
      params: { 
        tournament_id: tournamentId, 
        interval_seconds: intervalSeconds,
        start_hour: startHour,
        stop_hour: stopHour
      },
    })
    return response.data
  },

  /** Stop background job */
  stopBackgroundJob: async (tournamentId: number): Promise<{ message: string; status: string }> => {
    const response = await api.post('/admin/jobs/stop', null, {
      params: { tournament_id: tournamentId },
    })
    return response.data
  },

  /** Get background job status */
  getBackgroundJobStatus: async (tournamentId: number): Promise<{ 
    running: boolean; 
    status: string;
    start_hour?: number;
    stop_hour?: number;
    active_hours?: string;
    time_since_last_sync?: string;
    last_sync_timestamp?: string;
    last_sync_round?: number;
    debug_info?: any;
  }> => {
    const response = await api.get('/admin/jobs/status', {
      params: { tournament_id: tournamentId },
    })
    return response.data
  },

  /** Get Discord status */
  getDiscordStatus: async (): Promise<{
    enabled: boolean;
    webhook_configured: boolean;
    invite_url?: string;
    status: string;
  }> => {
    const response = await api.get<{
      enabled: boolean;
      webhook_configured: boolean;
      invite_url?: string;
      status: string;
    }>('/admin/discord/status')
    return response.data
  },

  /** Test Discord notification */
  testDiscordNotification: async (
    notificationType: string,
    tournamentId?: number
  ): Promise<{
    success: boolean;
    message: string;
    notification_type: string;
  }> => {
    const params: any = { notification_type: notificationType }
    if (tournamentId) params.tournament_id = tournamentId
    const response = await api.post('/admin/discord/test', null, { params })
    return response.data
  },

  /** List bonus points for a tournament */
  listBonusPoints: async (
    tournamentId: number, 
    roundId?: number
  ): Promise<{
    tournament_id: number;
    round_id?: number;
    bonus_points: Array<{
      id: number;
      entry_id: number;
      round_id: number;
      bonus_type: string;
      points: number;
      player_id: string;
      awarded_at: string;
    }>;
  }> => {
    const params: any = { tournament_id: tournamentId }
    if (roundId) params.round_id = roundId
    const response = await api.get('/admin/bonus-points/list', { params })
    return response.data
  },

  /** Delete a bonus point */
  deleteBonusPoint: async (bonusPointId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/admin/bonus-points/${bonusPointId}`)
    return response.data
  },

  /** Check all entry players for bonuses (manual) */
  checkAllPlayersForBonuses: async (
    tournamentId: number,
    roundId?: number
  ): Promise<{
    success: boolean;
    message: string;
    players_checked: number;
    scorecards_fetched: number;
    entries_processed: number;
    new_bonuses_found: number;
    errors: string[];
  }> => {
    const params: any = { tournament_id: tournamentId }
    if (roundId) params.round_id = roundId
    const response = await api.post('/admin/bonus-check/check-all-players', null, { params })
    return response.data
  },
}

// Ranking history endpoints
export const rankingHistoryApi = {
  /** Get ranking history for a tournament */
  getTournamentHistory: async (
    tournamentId: number,
    roundId?: number,
    entryId?: number
  ): Promise<{
    tournament: { id: number; name: string; year: number };
    snapshots: Array<{
      id: number;
      entry_id: number;
      entry_name: string;
      round_id: number;
      position: number;
      total_points: number;
      points_behind_leader: number;
      timestamp: string;
    }>;
    total_snapshots: number;
  }> => {
    const params: any = {}
    if (roundId) params.round_id = roundId
    if (entryId) params.entry_id = entryId
    const response = await api.get(`/ranking-history/tournament/${tournamentId}`, { params })
    return response.data
  },

  /** Get ranking history for a specific entry */
  getEntryHistory: async (
    entryId: number,
    tournamentId?: number
  ): Promise<{
    entry: { id: number; participant_name: string; tournament_id: number };
    snapshots: Array<{
      id: number;
      tournament_id: number;
      tournament_name: string;
      round_id: number;
      position: number;
      total_points: number;
      points_behind_leader: number;
      timestamp: string;
    }>;
    total_snapshots: number;
  }> => {
    const params: any = {}
    if (tournamentId) params.tournament_id = tournamentId
    const response = await api.get(`/ranking-history/entry/${entryId}`, { params })
    return response.data
  },

  /** Get ranking analytics for a tournament */
  getAnalytics: async (tournamentId: number): Promise<{
    tournament_id: number;
    tournament_name: string;
    biggest_movers: Array<{
      entry_id: number;
      entry_name: string;
      start_position: number;
      end_position: number;
      position_change: number;
      improvement: boolean;
    }>;
    position_distribution: Record<number, {
      position: number;
      unique_entries_count: number;
      unique_entries: string[];
      total_snapshots: number;
    }>;
    time_in_lead: Array<{
      entry_id: number;
      entry_name: string;
      seconds: number;
      hours: number;
      formatted: string;
    }>;
    total_snapshots: number;
  }> => {
    const response = await api.get(`/ranking-history/analytics/${tournamentId}`)
    return response.data
  },
}

export default api
