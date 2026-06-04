import { apiClient } from '@/api/client'
import type { AdminStudent, AdminMentor, GradingSession, Assignment, HealthResponse } from '@/types/api'

export const listStudents = async (): Promise<AdminStudent[]> => {
  const { data } = await apiClient.get<AdminStudent[]>('/admin/students')
  return data
}

export const listMentors = async (): Promise<AdminMentor[]> => {
  const { data } = await apiClient.get<AdminMentor[]>('/admin/mentors')
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

export const listAllSessions = async (): Promise<GradingSession[]> => {
  const { data } = await apiClient.get<GradingSession[]>('/admin/sessions')
  return data
}

export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await apiClient.get<HealthResponse>('/health', { baseURL: '' })
  return data
}
