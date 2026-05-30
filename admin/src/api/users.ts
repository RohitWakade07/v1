import { apiClient } from './client'

export interface Student {
  id: string
  roll_number: string
  full_name: string
  email: string
  is_active: boolean
  created_at: string
}

export interface Mentor {
  id: string
  username: string
  full_name: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export const listStudents = async (): Promise<Student[]> => {
  const { data } = await apiClient.get<Student[]>('/admin/students')
  return data
}

export const listMentors = async (): Promise<Mentor[]> => {
  const { data } = await apiClient.get<Mentor[]>('/admin/mentors')
  return data
}
