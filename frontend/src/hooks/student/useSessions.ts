import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSession, listSessions, startSession, createSession } from '@/api/student/sessions'

export const useSessions = (options?: { refetchInterval?: number | false }) =>
  useQuery({
    queryKey: ['sessions'],
    queryFn: listSessions,
    ...options,
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

export const useCreateSession = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (assignmentId: string) => createSession(assignmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
    },
  })
}
