import { useQuery } from '@tanstack/react-query'
import { fetchAssignments, fetchAssignment } from '@/api/assignments'
import { useAuthStore } from '@/store/authStore'

export function useAssignments() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['assignments'],
    queryFn: fetchAssignments,
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
