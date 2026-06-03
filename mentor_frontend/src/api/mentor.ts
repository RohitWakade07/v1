import { apiGet, apiPost } from './client'
import type { MentorStudent, MentorSession, MentorResult, MentorAnalytics, Classroom, ClassroomStudentEnrollment } from '@/types/api'

export async function fetchMentorStudents(): Promise<MentorStudent[]> {
  return apiGet<MentorStudent[]>('/mentor/students')
}

export async function fetchMentorSessions(): Promise<MentorSession[]> {
  return apiGet<MentorSession[]>('/mentor/sessions')
}

export async function fetchMentorResults(): Promise<MentorResult[]> {
  return apiGet<MentorResult[]>('/mentor/results')
}

export async function fetchMentorAnalytics(): Promise<MentorAnalytics> {
  return apiGet<MentorAnalytics>('/mentor/analytics/summary')
}

export async function fetchClassrooms(): Promise<Classroom[]> {
  return apiGet<Classroom[]>('/classrooms')
}

export async function createClassroom(name: string): Promise<Classroom> {
  return apiPost<Classroom, { name: string }>('/classrooms', { name })
}

export async function fetchClassroomEnrollments(classroomId: string): Promise<ClassroomStudentEnrollment[]> {
  return apiGet<ClassroomStudentEnrollment[]>(`/classrooms/${classroomId}/enrollments`)
}

export async function approveEnrollment(enrollmentId: string): Promise<any> {
  return apiPost<any, null>(`/classrooms/enrollments/${enrollmentId}/approve`, null)
}

export async function rejectEnrollment(enrollmentId: string): Promise<any> {
  return apiPost<any, null>(`/classrooms/enrollments/${enrollmentId}/reject`, null)
}
