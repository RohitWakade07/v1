import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSession, listSessions, startSession } from '@/api/sessions'

export const useSessions = () =>
  useQuery({
    queryKey: ['sessions'],
    queryFn: listSessions,
  })

export const useSession = (id?: string) =>
  useQuery({
    queryKey: ['sessions', id],
    queryFn: () => getSession(id ?? ''),
    enabled: Boolean(id),
  })

export const useStartSession = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => startSession(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      queryClient.setQueryData(['sessions', data.id], data)
    },
  })
}
