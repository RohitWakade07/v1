import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchMentorStudents,
  fetchMentorSessions,
  fetchMentorResults,
  fetchMentorSubmissions,
  fetchMentorAnalytics,
  fetchClassrooms,
  createClassroom,
  fetchClassroomEnrollments,
  approveEnrollment,
  rejectEnrollment,
} from '@/api/mentor/mentor'
import { useAuthStore } from '@/store/authStore'
import type { MentorStudent, MentorSession, MentorResult, MentorSubmission, MentorAnalytics, Classroom, ClassroomStudentEnrollment } from '@/types/api'

export function useMentorStudents() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery<MentorStudent[], Error>({
    queryKey: ['mentor-students'],
    queryFn: fetchMentorStudents,
    enabled: isAuthenticated,
  })
}

export function useMentorSessions() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery<MentorSession[], Error>({
    queryKey: ['mentor-sessions'],
    queryFn: fetchMentorSessions,
    enabled: isAuthenticated,
  })
}

export function useMentorResults() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery<MentorResult[], Error>({
    queryKey: ['mentor-results'],
    queryFn: fetchMentorResults,
    enabled: isAuthenticated,
  })
}

export function useMentorSubmissions() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery<MentorSubmission[], Error>({
    queryKey: ['mentor-submissions'],
    queryFn: fetchMentorSubmissions,
    enabled: isAuthenticated,
    refetchInterval: 10_000, // auto-refresh every 10s for live queue view
  })
}

export function useMentorAnalytics() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery<MentorAnalytics, Error>({
    queryKey: ['mentor-analytics'],
    queryFn: fetchMentorAnalytics,
    enabled: isAuthenticated,
  })
}

export function useClassrooms() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery<Classroom[], Error>({
    queryKey: ['classrooms'],
    queryFn: fetchClassrooms,
    enabled: isAuthenticated,
  })
}

export function useClassroomEnrollments(classroomId: string | null) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery<ClassroomStudentEnrollment[], Error>({
    queryKey: ['classroom-enrollments', classroomId],
    queryFn: () => fetchClassroomEnrollments(classroomId!),
    enabled: isAuthenticated && !!classroomId,
    staleTime: 0,
    refetchOnWindowFocus: true,
  })
}

export function useCreateClassroom() {
  const queryClient = useQueryClient()
  return useMutation<Classroom, Error, string>({
    mutationFn: createClassroom,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['classrooms'] })
    },
  })
}

export function useApproveEnrollment() {
  const queryClient = useQueryClient()
  return useMutation<unknown, Error, string>({
    mutationFn: approveEnrollment,
    onSuccess: () => {
      // Invalidate ALL classroom-enrollments queries (not just the current one)
      // to avoid stale-closure bugs when classroomId changes between renders.
      queryClient.invalidateQueries({ queryKey: ['classroom-enrollments'] })
      queryClient.invalidateQueries({ queryKey: ['mentor-students'] })
    },
  })
}

export function useRejectEnrollment() {
  const queryClient = useQueryClient()
  return useMutation<unknown, Error, string>({
    mutationFn: rejectEnrollment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['classroom-enrollments'] })
    },
  })
}
