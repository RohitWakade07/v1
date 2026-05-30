import { apiClient } from './client'

export interface HealthResponse {
  status: string
  database: string
  version?: string
}

export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}
