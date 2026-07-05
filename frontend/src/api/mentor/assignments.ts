import { apiGet, apiPost, apiPatch } from '@/api/client'
import type { Assignment, PaginatedResponse } from '@/types/api'

export interface AssignmentCreate {
  slug: string
  title: string
  description?: string
  category: string
  max_score?: number
  deadline?: string
}

export interface AssignmentUpdate {
  title?: string
  description?: string
  max_score?: number
  deadline?: string
}

export const fetchAssignments = (page = 1, limit = 20): Promise<PaginatedResponse<Assignment>> =>
  apiGet<PaginatedResponse<Assignment>>(`/mentor/assignments?page=${page}&limit=${limit}`)

export const fetchMentorAssignments = fetchAssignments

export const fetchAssignment = (id: string): Promise<Assignment> =>
  apiGet<Assignment>(`/mentor/assignments/${id}`)

export const createAssignment = (data: AssignmentCreate): Promise<Assignment> =>
  apiPost<Assignment, AssignmentCreate>('/assignments', data)

export const publishAssignment = (id: string): Promise<Assignment> =>
  apiPost<Assignment>(`/assignments/${id}/publish`, {})

export const unpublishAssignment = (id: string): Promise<Assignment> =>
  apiPost<Assignment>(`/assignments/${id}/unpublish`, {})

export const updateAssignment = (id: string, data: AssignmentUpdate): Promise<Assignment> =>
  apiPatch<Assignment, AssignmentUpdate>(`/assignments/${id}`, data)
