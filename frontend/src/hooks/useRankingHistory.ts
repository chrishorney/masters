/** React Query hooks for ranking history */
import { useQuery } from '@tanstack/react-query'
import { rankingHistoryApi } from '../services/api'
import type { RankingHistoryResponse, EntryRankingHistoryResponse, RankingAnalytics } from '../types'

/** Get ranking history for a tournament */
export function useTournamentRankingHistory(
  tournamentId: number | undefined,
  roundId?: number,
  entryId?: number
) {
  return useQuery<RankingHistoryResponse>({
    queryKey: ['ranking-history', 'tournament', tournamentId, roundId, entryId],
    queryFn: () => rankingHistoryApi.getTournamentHistory(tournamentId!, roundId, entryId),
    enabled: !!tournamentId,
    staleTime: 30000, // 30 seconds
  })
}

/** Get ranking history for a specific entry */
export function useEntryRankingHistory(
  entryId: number | undefined,
  tournamentId?: number
) {
  return useQuery<EntryRankingHistoryResponse>({
    queryKey: ['ranking-history', 'entry', entryId, tournamentId],
    queryFn: () => rankingHistoryApi.getEntryHistory(entryId!, tournamentId),
    enabled: !!entryId,
    staleTime: 30000,
  })
}

/** Get ranking analytics for a tournament */
export function useRankingAnalytics(tournamentId: number | undefined) {
  return useQuery<RankingAnalytics>({
    queryKey: ['ranking-analytics', tournamentId],
    queryFn: () => rankingHistoryApi.getAnalytics(tournamentId!),
    enabled: !!tournamentId,
    staleTime: 60000, // 1 minute
  })
}
