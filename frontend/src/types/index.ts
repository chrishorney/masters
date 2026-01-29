/** Type definitions for the application */

export interface Tournament {
  id: number
  year: number
  tourn_id: string
  org_id?: string
  name: string
  start_date: string
  end_date: string
  status: string
  current_round: number
}

export interface Participant {
  id: number
  name: string
  email?: string
  entry_date: string
  paid: boolean
}

export interface Entry {
  id: number
  participant_id: number
  tournament_id: number
  player1_id: string
  player2_id: string
  player3_id: string
  player4_id: string
  player5_id: string
  player6_id: string
  rebuy_player_ids: string[]
  rebuy_type?: string
  rebuy_original_player_ids: string[]
  weekend_bonus_earned: boolean
  weekend_bonus_forfeited: boolean
  created_at: string
  updated_at: string
  participant?: Participant
}

export interface DailyScore {
  id: number
  entry_id: number
  round_id: number
  date: string
  base_points: number
  bonus_points: number
  total_points: number
  details?: {
    base_breakdown?: Record<string, any>
    bonuses?: Array<{
      player_id?: string
      bonus_type: string
      points: number
    }>
  }
  calculated_at: string
}

export interface LeaderboardEntry {
  entry: Entry
  total_points: number
  daily_scores: DailyScore[]
  rank: number
}

export interface LeaderboardResponse {
  tournament: Tournament
  entries: LeaderboardEntry[]
  last_updated?: string
  view_type?: 'current' | 'round_snapshot'
  round_id?: number
  snapshot_timestamp?: string
}

export interface Player {
  player_id: string
  first_name: string
  last_name: string
  full_name: string
  position?: string
  status?: string
}

export interface RankingSnapshot {
  id: number
  entry_id: number
  entry_name: string
  round_id: number
  position: number
  total_points: number
  points_behind_leader: number
  timestamp: string
}

export interface RankingHistoryResponse {
  tournament: { id: number; name: string; year: number }
  snapshots: RankingSnapshot[]
  total_snapshots: number
}

export interface EntryRankingHistoryResponse {
  entry: { id: number; participant_name: string; tournament_id: number }
  snapshots: Array<{
    id: number
    tournament_id: number
    tournament_name: string
    round_id: number
    position: number
    total_points: number
    points_behind_leader: number
    timestamp: string
  }>
  total_snapshots: number
}

export interface RankingAnalytics {
  tournament_id: number
  tournament_name: string
  biggest_movers: Array<{
    entry_id: number
    entry_name: string
    start_position: number
    end_position: number
    position_change: number
    improvement: boolean
  }>
  position_distribution: Record<number, {
    position: number
    unique_entries_count: number
    unique_entries: string[]
    total_snapshots: number
  }>
  time_in_lead: Array<{
    entry_id: number
    entry_name: string
    seconds: number
    hours: number
    formatted: string
  }>
  total_snapshots: number
}
