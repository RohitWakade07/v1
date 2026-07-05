import { apiClient } from '@/api/client'
import type { AdminStudent, AdminMentor, GradingSession, AdminSubmission, Assignment, HealthResponse, PaginatedResponse, AdminClassroom } from '@/types/api'

export const listStudents = async (page = 1, limit = 20): Promise<PaginatedResponse<AdminStudent>> => {
  const { data } = await apiClient.get<PaginatedResponse<AdminStudent>>(`/admin/students?page=${page}&limit=${limit}`)
  return data
}

export const listMentors = async (page = 1, limit = 20): Promise<PaginatedResponse<AdminMentor>> => {
  const { data } = await apiClient.get<PaginatedResponse<AdminMentor>>(`/admin/mentors?page=${page}&limit=${limit}`)
  return data
}

export interface CreateMentorPayload {
  username: string
  full_name: string
  email: string
  password: string
  role: 'mentor' | 'admin'
}

export const createMentor = async (payload: CreateMentorPayload): Promise<AdminMentor> => {
  const { data } = await apiClient.post<AdminMentor>('/admin/mentors', payload)
  return data
}

export const listAllAssignments = async (): Promise<Assignment[]> => {
  const { data } = await apiClient.get<Assignment[]>('/admin/assignments/all')
  return data
}

export const publishAssignment = async (id: string): Promise<Assignment> => {
  const { data } = await apiClient.post<Assignment>(`/assignments/${id}/publish`)
  return data
}

export const unpublishAssignment = async (id: string): Promise<Assignment> => {
  const { data } = await apiClient.post<Assignment>(`/assignments/${id}/unpublish`)
  return data
}

export interface AdminAssignmentUpdate {
  title?: string
  description?: string
  max_score?: number
  deadline?: string
  is_published?: boolean
  is_archived?: boolean
  resource_links?: Array<{ title: string; url: string; type?: string }>
  late_penalty_pct?: number
  submission_filename?: string
  submission_instructions?: string
  expected_structure?: string
  expected_media_url?: string
}

export const adminUpdateAssignment = async (id: string, payload: AdminAssignmentUpdate): Promise<Assignment> => {
  const { data } = await apiClient.patch<Assignment>(`/assignments/admin/${id}`, payload)
  return data
}

export const listAllSessions = async (page = 1, limit = 20): Promise<PaginatedResponse<GradingSession>> => {
  const { data } = await apiClient.get<PaginatedResponse<GradingSession>>(`/admin/sessions?page=${page}&limit=${limit}`)
  return data
}

export const listAllSubmissions = async (page = 1, limit = 20): Promise<PaginatedResponse<AdminSubmission>> => {
  const { data } = await apiClient.get<PaginatedResponse<AdminSubmission>>(`/admin/submissions?page=${page}&limit=${limit}`)
  return data
}

export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}

export const deleteAssignment = async (assignmentId: string): Promise<void> => {
  await apiClient.delete(`/assignments/admin/${assignmentId}`);
};

export const getMentorDetails = async (mentorId: string): Promise<AdminMentor> => {
  const { data } = await apiClient.get<AdminMentor>(`/admin/mentors/${mentorId}`)
  return data
}

export const listMentorClassrooms = async (mentorId: string): Promise<AdminClassroom[]> => {
  const { data } = await apiClient.get<AdminClassroom[]>(`/admin/mentors/${mentorId}/classrooms`)
  return data
}

export const getClassroomDetails = async (classroomId: string): Promise<AdminClassroom> => {
  const { data } = await apiClient.get<AdminClassroom>(`/admin/classrooms/${classroomId}`)
  return data
}

export const listClassroomStudents = async (classroomId: string, page = 1, limit = 20): Promise<PaginatedResponse<AdminStudent>> => {
  const { data } = await apiClient.get<PaginatedResponse<AdminStudent>>(`/admin/classrooms/${classroomId}/students?page=${page}&limit=${limit}`)
  return data
}

export const listClassroomSessions = async (classroomId: string, page = 1, limit = 20): Promise<PaginatedResponse<GradingSession>> => {
  const { data } = await apiClient.get<PaginatedResponse<GradingSession>>(`/admin/classrooms/${classroomId}/sessions?page=${page}&limit=${limit}`)
  return data
}
