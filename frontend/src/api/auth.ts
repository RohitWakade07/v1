import { apiClient } from './client'
import type { StudentAuthResponse, StudentProfile } from '@/types/api'

export interface StudentLoginRequest {
  roll_number: string
  password: string
}

export interface StudentRegisterRequest {
  full_name: string
  email: string
  roll_number: string
  password: string
}

export const registerStudent = async (payload: StudentRegisterRequest) => {
  const { data } = await apiClient.post<any>(
    '/auth/student/register',
    payload,
  )
  return data
}

export const loginStudent = async (payload: StudentLoginRequest) => {
  const { data } = await apiClient.post<StudentAuthResponse>(
    '/auth/student/login',
    payload,
  )
  return data
}

export const getProfile = async () => {
  const { data } = await apiClient.get<StudentProfile>('/students/me')
  return data
}
