import { apiGet, apiPost } from '@/api/client'
import type {
  MentorStudent, MentorSession, MentorResult, MentorAnalytics,
  Classroom, ClassroomStudentEnrollment,
} from '@/types/api'

export const fetchMentorStudents = (): Promise<MentorStudent[]> =>
  apiGet<MentorStudent[]>('/mentor/students')

export const fetchMentorSessions = (): Promise<MentorSession[]> =>
  apiGet<MentorSession[]>('/mentor/sessions')

export const fetchMentorResults = (): Promise<MentorResult[]> =>
  apiGet<MentorResult[]>('/mentor/results')

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
