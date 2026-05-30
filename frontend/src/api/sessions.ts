import { apiClient } from './client'
import type { SessionDetail, SessionSummary } from '@/types/api'

export const listSessions = async () => {
  const { data } = await apiClient.get<any[]>('/sessions/')
  return data.map(s => ({
    ...s,
    id: s.session_id
  })) as SessionSummary[]
}

export const getSession = async (id: string) => {
  const { data } = await apiClient.get<any>(`/sessions/${id}`)
  return {
    ...data,
    id: data.session_id
  } as SessionDetail
}

export const createSession = async (assignment_id: string) => {
  const { data } = await apiClient.post<any>('/sessions/', {
    assignment_id,
  })
  return {
    ...data,
    id: data.session_id
  } as SessionSummary
}

export const startSession = async (id: string) => {
  const { data } = await apiClient.patch<any>(`/sessions/${id}/start`)
  return {
    ...data,
    id: data.session_id
  } as SessionSummary
}
