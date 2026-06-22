import { apiClient } from '@/api/client'
import type { AdminStudent, AdminMentor, GradingSession, AdminSubmission, Assignment, HealthResponse } from '@/types/api'

export const listStudents = async (): Promise<AdminStudent[]> => {
  const { data } = await apiClient.get<AdminStudent[]>('/admin/students')
  return data
}

export const listMentors = async (): Promise<AdminMentor[]> => {
  const { data } = await apiClient.get<AdminMentor[]>('/admin/mentors')
  return data
}

export interface CreateMentorPayload {
  username: string
  full_name: string
  email: string
  password: string
  role: 'mentor' | 'admin'
}

export const createMentor = async (payload: CreateMentorPayload): Promise<AdminMentor> => {
  const { data } = await apiClient.post<AdminMentor>('/admin/mentors', payload)
  return data
}

export const listAllAssignments = async (): Promise<Assignment[]> => {
  const { data } = await apiClient.get<Assignment[]>('/admin/assignments/all')
  return data
}

export const publishAssignment = async (id: string): Promise<Assignment> => {
  const { data } = await apiClient.post<Assignment>(`/assignments/${id}/publish`)
  return data
}

export const unpublishAssignment = async (id: string): Promise<Assignment> => {
  const { data } = await apiClient.post<Assignment>(`/assignments/${id}/unpublish`)
  return data
}

export interface AdminAssignmentUpdate {
  title?: string
  description?: string
  max_score?: number
  deadline?: string
  is_published?: boolean
  is_archived?: boolean
  resource_links?: Array<{ title: string; url: string; type?: string }>
  late_penalty_pct?: number
  submission_filename?: string
  submission_instructions?: string
}

export const adminUpdateAssignment = async (id: string, payload: AdminAssignmentUpdate): Promise<Assignment> => {
  const { data } = await apiClient.patch<Assignment>(`/assignments/admin/${id}`, payload)
  return data
}

export const listAllSessions = async (): Promise<GradingSession[]> => {
  const { data } = await apiClient.get<GradingSession[]>('/admin/sessions')
  return data
}

export const listAllSubmissions = async (): Promise<AdminSubmission[]> => {
  const { data } = await apiClient.get<AdminSubmission[]>('/admin/submissions')
  return data
}

export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}
