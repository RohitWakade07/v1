import { apiClient } from '@/api/client'
import type { SessionSummary, SessionDetail } from '@/types/api'

export const listSessions = async (): Promise<SessionSummary[]> => {
  const { data } = await apiClient.get<SessionSummary[]>('/sessions')
  return data.map((s: SessionSummary & { session_id?: string }) => ({
    ...s,
    id: s.session_id ?? s.id,
  }))
}

export const getSession = async (id: string): Promise<SessionDetail> => {
  const { data } = await apiClient.get<SessionDetail>(`/sessions/${id}`)
  return data
}

export const createSession = async (assignment_id: string): Promise<SessionSummary> => {
  const { data } = await apiClient.post<SessionSummary>('/sessions', { assignment_id })
  return { ...data, id: (data as SessionSummary & { session_id?: string }).session_id ?? data.id }
}

export const startSession = async (id: string): Promise<SessionSummary> => {
  const { data } = await apiClient.patch<SessionSummary>(`/sessions/${id}/start`)
  return data
}

export const abortSession = async (id: string): Promise<SessionSummary> => {
  const { data } = await apiClient.post<SessionSummary>(`/sessions/${id}/abort`)
  return data
}
