/** React Query hooks for tournament data */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tournamentApi, scoresApi } from '../services/api'

/** Get current tournament */
export function useCurrentTournament() {
  return useQuery({
    queryKey: ['tournament', 'current'],
    queryFn: () => tournamentApi.getCurrent(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/** Get tournament by ID */
export function useTournament(id: number | undefined) {
  return useQuery({
    queryKey: ['tournament', id],
    queryFn: () => tournamentApi.getById(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })
}

/** Sync tournament data */
export function useSyncTournament() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ orgId, tournId, year }: { orgId?: string; tournId?: string; year?: number }) =>
      tournamentApi.sync(orgId, tournId, year),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tournament'] })
      queryClient.invalidateQueries({ queryKey: ['leaderboard'] })
    },
  })
}

/** Get leaderboard */
export function useLeaderboard(tournamentId: number | undefined) {
  return useQuery({
    queryKey: ['leaderboard', tournamentId],
    queryFn: () => scoresApi.getLeaderboard(tournamentId!),
    enabled: !!tournamentId,
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    staleTime: 10 * 1000, // Consider stale after 10 seconds
  })
}

/** Calculate scores */
export function useCalculateScores() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ tournamentId, roundId }: { tournamentId: number; roundId?: number }) =>
      scoresApi.calculateScores(tournamentId, roundId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leaderboard'] })
      queryClient.invalidateQueries({ queryKey: ['scores'] })
    },
  })
}
