import { apiClient } from './client'
import type { SessionDetail, SessionSummary } from '@/types/api'

export const listSessions = async () => {
  const { data } = await apiClient.get<SessionSummary[]>('/sessions/')
  return data
}

export const getSession = async (id: string) => {
  const { data } = await apiClient.get<SessionDetail>(`/sessions/${id}`)
  return data
}

export const createSession = async (assignment_id: string) => {
  const { data } = await apiClient.post<SessionSummary>('/sessions/', {
    assignment_id,
  })
  return data
}

export const startSession = async (id: string) => {
  const { data } = await apiClient.patch<SessionSummary>(`/sessions/${id}/start`)
  return data
}
