import { useQuery } from '@tanstack/react-query'
import { getSession, listSessions } from '@/api/sessions'

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
