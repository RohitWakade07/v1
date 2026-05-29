import { apiClient } from './client'
import type { ResultDetail, ResultSummary } from '@/types/api'

export const listResults = async () => {
  const { data } = await apiClient.get<ResultSummary[]>('/results/')
  return data
}

export const getResult = async (id: string) => {
  const { data } = await apiClient.get<ResultDetail>(`/results/${id}`)
  return data
}
