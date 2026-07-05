import { useQuery } from '@tanstack/react-query'
import { fetchAssignments, fetchAssignment } from '@/api/mentor/assignments'
import { useAuthStore } from '@/store/authStore'

export function useAssignments(page = 1, limit = 20) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['assignments', page, limit],
    queryFn: () => fetchAssignments(page, limit),
    enabled: isAuthenticated,
  })
}

export function useAssignment(id?: string) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['assignments', id],
    queryFn: () => fetchAssignment(id!),
    enabled: isAuthenticated && !!id,
  })
}
