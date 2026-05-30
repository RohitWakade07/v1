import { useQuery } from '@tanstack/react-query'
import { fetchMentorStudents, fetchMentorSessions, fetchMentorResults, fetchMentorAnalytics } from '@/api/mentor'
import { useAuthStore } from '@/store/authStore'

export function useMentorStudents() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['mentor-students'],
    queryFn: fetchMentorStudents,
    enabled: isAuthenticated,
  })
}

export function useMentorSessions() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['mentor-sessions'],
    queryFn: fetchMentorSessions,
    enabled: isAuthenticated,
  })
}

export function useMentorResults() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['mentor-results'],
    queryFn: fetchMentorResults,
    enabled: isAuthenticated,
  })
}

export function useMentorAnalytics() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['mentor-analytics'],
    queryFn: fetchMentorAnalytics,
    enabled: isAuthenticated,
  })
}
