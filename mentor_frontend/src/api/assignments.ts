import { apiGet, apiPost, apiPatch } from './client'
import type { Assignment, AssignmentCreate, AssignmentUpdate } from '@/types/api'

export async function fetchAssignments(): Promise<Assignment[]> {
  return apiGet<Assignment[]>('/mentor/assignments')
}

export async function fetchAssignment(id: string): Promise<Assignment> {
  return apiGet<Assignment>(`/assignments/${id}`)
}

export async function createAssignment(data: AssignmentCreate): Promise<Assignment> {
  return apiPost<Assignment, AssignmentCreate>('/assignments/', data)
}

export async function publishAssignment(id: string): Promise<Assignment> {
  return apiPost<Assignment>(`/assignments/${id}/publish`, {})
}

export async function unpublishAssignment(id: string): Promise<Assignment> {
  return apiPost<Assignment>(`/assignments/${id}/unpublish`, {})
}

export async function updateAssignment(id: string, data: AssignmentUpdate): Promise<Assignment> {
  return apiPatch<Assignment, AssignmentUpdate>(`/assignments/${id}`, data)
}
