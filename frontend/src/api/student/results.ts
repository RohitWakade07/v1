import { apiClient } from '@/api/client'
import type { ResultSummary, ResultDetail } from '@/types/api'

export const listResults = async (): Promise<ResultSummary[]> => {
  const { data } = await apiClient.get<ResultSummary[]>('/results/')
  return data
}

export const getResult = async (id: string): Promise<ResultDetail> => {
  const { data } = await apiClient.get<ResultDetail>(`/results/${id}`)
  return data
}
