import { apiGet, apiPost } from '@/api/client'
import type {
  MentorStudent, MentorSession, MentorResult, MentorSubmission, MentorAnalytics,
  Classroom, ClassroomStudentEnrollment,
} from '@/types/api'

export const fetchMentorStudents = (): Promise<MentorStudent[]> =>
  apiGet<MentorStudent[]>('/mentor/students')

export const fetchMentorSessions = (): Promise<MentorSession[]> =>
  apiGet<MentorSession[]>('/mentor/sessions')

export const fetchMentorResults = (): Promise<MentorResult[]> =>
  apiGet<MentorResult[]>('/mentor/results')

export const fetchMentorSubmissions = (): Promise<MentorSubmission[]> =>
  apiGet<MentorSubmission[]>('/mentor/submissions')

export const fetchMentorAnalytics = (): Promise<MentorAnalytics> =>
  apiGet<MentorAnalytics>('/mentor/analytics/summary')

export const fetchClassrooms = (): Promise<Classroom[]> =>
  apiGet<Classroom[]>('/classrooms')

export const createClassroom = (name: string): Promise<Classroom> =>
  apiPost<Classroom, { name: string }>('/classrooms', { name })

export const fetchClassroomEnrollments = (classroomId: string): Promise<ClassroomStudentEnrollment[]> =>
  apiGet<ClassroomStudentEnrollment[]>(`/classrooms/${classroomId}/enrollments`)

export const approveEnrollment = (enrollmentId: string): Promise<unknown> =>
  apiPost(`/classrooms/enrollments/${enrollmentId}/approve`, null)

export const rejectEnrollment = (enrollmentId: string): Promise<unknown> =>
  apiPost(`/classrooms/enrollments/${enrollmentId}/reject`, null)

export const importStudentsCSV = async (classroomId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  const { apiClient } = await import('@/api/client')
  const { data } = await apiClient.post(`/mentor/students/csv?classroom_id=${classroomId}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const downloadStudentCSVTemplate = () => {
  const csv = `full_name,email,roll_number\nJohn Doe,john@example.com,2024CSE001\nJane Smith,jane@example.com,2024CSE002`
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'student_import_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}
