import { apiClient, apiPost } from './client'
import type { StudentAuthResponse, StudentProfile, MentorLoginRequest, TokenResponse } from '@/types/api'

// ── Student auth ──────────────────────────────────────────────────

export interface StudentRegisterRequest {
  full_name: string
  email: string
  roll_number: string
  password: string
  class_code?: string
}

export const registerStudent = async (payload: StudentRegisterRequest) => {
  const { data } = await apiClient.post<unknown>('/auth/student/register', payload)
  return data
}

export const loginStudent = async (roll_number: string, password: string): Promise<StudentAuthResponse> => {
  const { data } = await apiClient.post<StudentAuthResponse>('/auth/student/login', {
    roll_number,
    password,
  })
  return data
}

export const getStudentProfile = async (): Promise<StudentProfile> => {
  const { data } = await apiClient.get<StudentProfile>('/students/me')
  return data
}

export const joinClassroom = async (classCode: string) => {
  const { data } = await apiClient.post<{ message: string }>('/classrooms/join', {
    class_code: classCode,
  })
  return data
}

// ── Mentor / Admin auth ───────────────────────────────────────────

export const loginStaff = async (credentials: MentorLoginRequest): Promise<TokenResponse> =>
  apiPost<TokenResponse, MentorLoginRequest>('/auth/mentor/login', credentials)
