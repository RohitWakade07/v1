export type UserRole = 'student' | 'mentor' | 'admin'

export type SessionStatus = 'STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED'

export type AssignmentCategory =
  | 'artifact_validation'
  | 'deterministic_execution'
  | 'filesystem_validation'
  | 'git_validation'
  | 'network_validation'
  | 'documentation_review'
  | 'manual_review'

export interface Assignment {
  id: string           // UUID
  slug: string
  title: string
  description: string | null
  category: AssignmentCategory
  max_score: number
  deadline: string | null    // ISO8601
  is_published: boolean
  created_by_id: string      // UUID
  created_at: string         // ISO8601
  updated_at: string         // ISO8601
}

export interface AssignmentCreate {
  slug: string
  title: string
  description?: string
  category: AssignmentCategory
  max_score?: number
  deadline?: string
}

export interface AssignmentUpdate {
  title?: string
  description?: string
  max_score?: number
  deadline?: string
}

export interface MentorLoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  role: UserRole
  subject_id: string
}

export interface ErrorResponse {
  detail: string
  code?: string
}

export interface MentorStudent {
  id: string
  roll_number: string
  full_name: string
  email: string
  assignments_participated: number
  sessions_count: number
}

export interface MentorSession {
  id: string
  student_roll: string
  student_name: string
  assignment_slug: string
  assignment_title: string
  status: SessionStatus
  started_at: string
  completed_at: string | null
  final_score: number | null
}

export interface MentorResult {
  session_id: string
  student_roll: string
  student_name: string
  assignment_slug: string
  assignment_title: string
  final_score: number
  max_score: number
  completed_at: string
}

export interface MentorAnalytics {
  total_students: number
  completion_rate: number
  avg_score: number
  total_submissions: number
  score_distribution: Record<string, number>
  assignments_participation: Record<string, number>
  category_breakdown: Record<string, number>
}
