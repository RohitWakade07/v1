import { apiClient } from './client'

export interface GradingSession {
  id: string
  student_id: string
  assignment_id: string
  status: string
  started_at: string
  submitted_at?: string
  completed_at?: string
  final_score?: number
  rejection_reason?: string
}

export const listAllSessions = async (): Promise<GradingSession[]> => {
  const { data } = await apiClient.get<GradingSession[]>('/admin/sessions')
  return data
}
