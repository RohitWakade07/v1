import { apiClient } from '@/api/client'

export interface QuizPublic {
  id: string
  assignment_id: string
  title: string
  marks_per_question: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface QuizOption {
  id: string
  option_text: string
  order_index: number
  is_correct?: boolean
}

export interface QuizQuestion {
  id: string
  question_text: string
  type: 'single' | 'multiple'
  marks: number | null
  order_index: number
  options: QuizOption[]
}

export interface QuizAttemptResult {
  attempt_id: string
  quiz_id: string
  total_score: number
  max_score: number
  submitted_at: string | null
  question_results: Array<{
    question_id: string
    question_text: string
    is_correct: boolean
    marks_awarded: number
    marks_possible: number
    correct_option_ids?: string[]
    selected_option_ids: string[]
  }>
}

// Student
export const getStudentQuiz = async (assignmentId: string) => {
  const { data } = await apiClient.get<QuizPublic>(`/student/assignments/${assignmentId}/quiz`)
  return data
}

export const getStudentQuizQuestions = async (quizId: string) => {
  const { data } = await apiClient.get<QuizQuestion[]>(`/student/quizzes/${quizId}/questions`)
  return data
}

export const submitQuizAttempt = async (quizId: string, answers: Record<string, string[]>) => {
  const { data } = await apiClient.post<QuizAttemptResult>(`/student/quizzes/${quizId}/attempt`, { answers })
  return data
}

export const getQuizResult = async (quizId: string) => {
  const { data } = await apiClient.get<QuizAttemptResult>(`/student/quizzes/${quizId}/result`)
  return data
}

// Admin
export const getAdminQuiz = async (assignmentId: string) => {
  const { data } = await apiClient.get<QuizPublic>(`/admin/assignments/${assignmentId}/quiz`)
  return data
}

export const createAdminQuiz = async (assignmentId: string, payload: { title: string; marks_per_question: number; is_active: boolean }) => {
  const { data } = await apiClient.post<QuizPublic>(`/admin/assignments/${assignmentId}/quiz`, payload)
  return data
}

export const updateAdminQuiz = async (quizId: string, payload: Partial<{ title: string; marks_per_question: number; is_active: boolean }>) => {
  const { data } = await apiClient.patch<QuizPublic>(`/admin/quizzes/${quizId}`, payload)
  return data
}

export const getAdminQuizQuestions = async (quizId: string) => {
  const { data } = await apiClient.get<QuizQuestion[]>(`/admin/quizzes/${quizId}/questions`)
  return data
}

export const addQuestion = async (quizId: string, payload: Omit<QuizQuestion, 'id' | 'created_at' | 'options'> & { options: Array<{ option_text: string; is_correct: boolean; order_index: number }> }) => {
  const { data } = await apiClient.post<QuizQuestion>(`/admin/quizzes/${quizId}/questions`, payload)
  return data
}

export const editQuestion = async (questionId: string, payload: any) => {
  const { data } = await apiClient.patch<QuizQuestion>(`/admin/questions/${questionId}`, payload)
  return data
}

export const deleteQuestion = async (questionId: string) => {
  await apiClient.delete(`/admin/questions/${questionId}`)
}

export const importQuestionsCSV = async (quizId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<QuizQuestion[]>(`/admin/quizzes/${quizId}/questions/csv`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const downloadQuizCSVTemplate = () => {
  const csv = `question,option_a,option_b,option_c,option_d,correct_answer,type,marks\nWhat is 2+2?,3,4,5,6,b,single,1\nWhich are prime numbers?,2,4,7,9,"a,c",multiple,2`
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'quiz_questions_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}
