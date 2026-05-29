import { apiClient } from './client'
import type { AssignmentDetail, AssignmentSummary } from '@/types/api'

export const listAssignments = async () => {
  const { data } = await apiClient.get<AssignmentSummary[]>('/assignments/')
  return data
}

export const getAssignment = async (id: string) => {
  const { data } = await apiClient.get<AssignmentDetail>(`/assignments/${id}`)
  return data
}
