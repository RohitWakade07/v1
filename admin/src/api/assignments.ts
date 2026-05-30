import { apiClient } from './client'

// BUG FIX: Assignment interface was missing the is_archived field
// that exists on the backend AssignmentPublic schema and in the DB.
// This caused TypeScript to silently discard the field and meant
// any UI logic checking is_archived would always get `undefined`.
export interface Assignment {
  id: string
  slug: string
  title: string
  description?: string | null
  category: string
  max_score: number
  deadline?: string | null
  is_published: boolean
  is_archived: boolean        // FIX: was missing
  created_by_id: string
  created_at: string
  updated_at: string
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
