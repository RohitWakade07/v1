import { apiClient } from './client'

export interface LoginResponse {
  access_token: string
  token_type: string
  role: string
  subject_id: string
  expires_in: number
}

export const loginAdmin = async (username: string, password: string): Promise<LoginResponse> => {
  const { data } = await apiClient.post<LoginResponse>('/auth/mentor/login', {
    username,
    password,
  })
  return data
}
