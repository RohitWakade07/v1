import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchMentorStudents,
  fetchMentorSessions,
  fetchMentorResults,
  fetchMentorAnalytics,
  fetchClassrooms,
  createClassroom,
  fetchClassroomEnrollments,
  approveEnrollment,
  rejectEnrollment,
} from '@/api/mentor'
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

export function useClassrooms() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['classrooms'],
    queryFn: fetchClassrooms,
    enabled: isAuthenticated,
  })
}

export function useClassroomEnrollments(classroomId: string | null) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['classroom-enrollments', classroomId],
    queryFn: () => fetchClassroomEnrollments(classroomId!),
    enabled: isAuthenticated && !!classroomId,
    staleTime: 0,
    refetchOnWindowFocus: true,
  })
}

export function useCreateClassroom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createClassroom,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['classrooms'] })
    },
  })
}

export function useApproveEnrollment(classroomId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: approveEnrollment,
    onSuccess: () => {
      // Invalidate ALL classroom-enrollments queries (not just the current one)
      // to avoid stale-closure bugs when classroomId changes between renders.
      queryClient.invalidateQueries({ queryKey: ['classroom-enrollments'] })
      queryClient.invalidateQueries({ queryKey: ['mentor-students'] })
    },
  })
}

export function useRejectEnrollment(classroomId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: rejectEnrollment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['classroom-enrollments'] })
    },
  })
}
