import { useQuery } from '@tanstack/react-query'
import { getAssignment, listAssignments } from '@/api/assignments'

export const useAssignments = () =>
  useQuery({
    queryKey: ['assignments'],
    queryFn: listAssignments,
  })

export const useAssignment = (id?: string) =>
  useQuery({
    queryKey: ['assignments', id],
    queryFn: () => getAssignment(id ?? ''),
    enabled: Boolean(id),
  })
