import { apiClient } from '@/api/client'
import type { AssignmentSummary, AssignmentDetail } from '@/types/api'

export const listAssignments = async (): Promise<AssignmentSummary[]> => {
  const { data } = await apiClient.get<AssignmentSummary[]>('/assignments')
  return data
}

export const getAssignment = async (id: string): Promise<AssignmentDetail> => {
  const { data } = await apiClient.get<AssignmentDetail>(`/assignments/${id}`)
  return data
}
