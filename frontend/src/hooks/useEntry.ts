/** React Query hooks for entry data */
import { useQuery } from '@tanstack/react-query'
import { entryApi } from '../services/api'

/** Get entry details */
export function useEntryDetails(entryId: number | undefined) {
  return useQuery({
    queryKey: ['entry', entryId],
    queryFn: () => entryApi.getEntryDetails(entryId!),
    enabled: !!entryId,
    staleTime: 30 * 1000, // 30 seconds
  })
}
