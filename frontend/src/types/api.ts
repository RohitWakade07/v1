export type AssignmentCategory =
  | 'artifact_validation'
  | 'deterministic_execution'
  | 'filesystem_validation'
  | 'git_validation'
  | 'network_validation'
  | 'documentation_review'
  | 'manual_review'

export type SessionStatus =
  | 'CREATED'
  | 'CHALLENGE_ISSUED'
  | 'RUNNING'
  | 'ABORTED'
  | 'PROOF_GENERATED'
  | 'PROOF_SUBMITTED'
  | 'VERIFIED'
  | 'FAILED'
  | 'STARTED'
  | 'IN_PROGRESS'
  | 'SUBMITTED'
  | 'COMPLETED'
  | 'REJECTED'

export interface StudentAuthResponse {
  access_token: string
  token_type: 'bearer'
  role: 'student'
  roll_number: string
  student_uuid: string
}

export interface StudentProfile {
  full_name?: string
  email?: string
  roll_number: string
  student_uuid: string
  role: 'student'
  classroom_name?: string | null
  classroom_status?: string | null
  mentor_name?: string | null
}

export interface AssignmentSummary {
  id: string
  title: string
  description?: string
  category: AssignmentCategory
  max_score: number
  deadline?: string
  published: boolean
  created_at?: string
}

export interface AssignmentDetail extends AssignmentSummary {
  instructions?: string
}

export interface SessionSummary {
  id: string
  assignment_id: string
  status: SessionStatus
  started_at?: string
  submitted_at?: string
  completed_at?: string
  final_score?: number | null
  proof_nonce?: string | null
  rejection_reason?: string | null
}

export interface SessionDetail extends SessionSummary {
  assignment_title?: string
  score_breakdown?: Record<string, { passed: boolean; score: number }>
}

export interface ResultSummary {
  id: string
  assignment_id: string
  assignment_title: string
  category: AssignmentCategory
  final_score: number
  max_score: number
  completed_at: string
}

export interface ResultDetail extends ResultSummary {
  score_breakdown: Record<string, { passed: boolean; score: number }>
  certificate_available?: boolean
}

export interface ProofTestResult {
  test_id: string
  passed: boolean
  stdout_hash?: string | null
  stderr_hash?: string | null
  exit_code?: number
  score: number
}

export interface ProofSubmitRequest {
  session_id: string
  assignment_id: string
  student_id: string
  timestamp: string
  nonce: string
  grader_binary_hash: string
  results: Record<string, ProofTestResult>
  artifact_hashes: Record<string, string>
  hmac_signature: string
}

export interface ProofSubmitResponse {
  session_id: string
  status: SessionStatus
  final_score?: number | null
  message: string
}
