import { useQuery } from '@tanstack/react-query'
import { getStudentAllQuizResults, type QuizAttemptSummary } from '@/api/student/quiz'
import { useAuthStore } from '@/store/authStore'

export const useQuizResults = (options?: { refetchInterval?: number }) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const role = useAuthStore((s) => s.role)

  return useQuery<QuizAttemptSummary[]>({
    queryKey: ['student-quiz-results'],
    queryFn: getStudentAllQuizResults,
    enabled: isAuthenticated && role === 'student',
    refetchInterval: options?.refetchInterval,
  })
}
