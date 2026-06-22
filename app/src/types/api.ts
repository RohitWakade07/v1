// ── Shared API types (merged from student, mentor, admin) ────────────

export type UserRole = 'student' | 'mentor' | 'admin'

// ─── Auth ──────────────────────────────────────────────────────────
export interface StudentAuthResponse {
  access_token: string
  token_type: 'bearer'
  role: 'student'
  roll_number: string
  student_uuid: string
}

export interface MentorAuthResponse {
  access_token: string
  token_type: 'bearer'
  role: 'mentor' | 'admin'
  subject_id: string
  username?: string
  mentor_uuid?: string
  expires_in?: number
}

// ─── Student profile ───────────────────────────────────────────────
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

// ─── Assignment ────────────────────────────────────────────────────
export type AssignmentCategory =
  | 'artifact_validation'
  | 'deterministic_execution'
  | 'filesystem_validation'
  | 'git_validation'
  | 'network_validation'
  | 'documentation_review'
  | 'manual_review'

export interface AssignmentSummary {
  id: string
  title: string
  description?: string
  category: AssignmentCategory
  max_score: number
  deadline?: string
  published?: boolean
  created_at?: string
}

export interface AssignmentDetail extends AssignmentSummary {
  slug?: string
  instructions?: string
  resource_links?: { title: string; url: string }[] | null
  allow_late_submissions?: boolean
  late_penalty_pct?: number
  submission_filename?: string | null
  submission_instructions?: string | null
}

// Full assignment (used by mentor + admin)
export interface Assignment {
  id: string
  slug: string
  title: string
  description?: string | null
  category: string
  max_score: number
  deadline?: string | null
  is_published: boolean
  is_archived: boolean
  late_penalty_pct?: number
  resource_links?: Array<{ title: string; url: string; type?: string }> | null
  submission_filename?: string | null
  submission_instructions?: string | null
  created_by_id: string
  created_at: string
  updated_at?: string
}

// ─── Session ───────────────────────────────────────────────────────
export type SessionStatus =
  | 'CREATED' | 'CHALLENGE_ISSUED' | 'RUNNING' | 'ABORTED'
  | 'PROOF_GENERATED' | 'PROOF_SUBMITTED' | 'VERIFIED' | 'FAILED'
  | 'STARTED' | 'IN_PROGRESS' | 'SUBMITTED' | 'COMPLETED' | 'REJECTED'

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

// ─── Result ────────────────────────────────────────────────────────
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

// ─── Submission & V2 Result ──────────────────────────────────────────
export type SubmissionSourceType = 'github' | 'zip'

export type SubmissionStatus =
  | 'PENDING' | 'QUEUED' | 'RUNNING' | 'COMPLETED'
  | 'FAILED' | 'TIMEOUT' | 'CANCELLED' | 'VALIDATION_ERROR'

export interface SubmissionPublic {
  id: string
  assignment_id: string
  student_id: string
  status: SubmissionStatus
  source_type: SubmissionSourceType
  repo_url?: string | null
  zip_object_key?: string | null
  submitted_at: string
  attempt_number: number
}

export interface SubmissionCreateResponse extends SubmissionPublic {}

export interface CheckResult {
  name: string
  passed: boolean
  marks: number
  max_marks: number
  reason: string
  hint: string
}

export interface SubmissionResultDetail {
  id: string
  submission_id: string
  checks_json: string | null
  feedback: string | null
  stdout: string | null
  stderr: string | null
  execution_command: string | null
  exit_code: number | null
  execution_time_ms: number | null
  timed_out: boolean
  oom_killed: boolean
  container_id: string | null
  grader_logs: string | null
  ai_feedback: string | null
  created_at: string
}

// ─── Proof (Legacy, Keep for now if needed by other components) ─────
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
  status: string
  final_score?: number | null
  message: string
}

// ─── Mentor-scoped types ───────────────────────────────────────────
export interface MentorStudent {
  id: string
  roll_number: string
  full_name: string
  email: string
  classroom_name?: string
  enrollment_status?: string
  assignments_participated?: number
  sessions_count?: number
}

export interface MentorSession {
  id: string
  student_roll?: string
  student_name: string
  assignment_slug?: string
  assignment_title: string
  status: string
  started_at?: string
  completed_at?: string | null
  final_score?: number | null
}

export interface MentorResult {
  id?: string
  session_id?: string
  student_roll?: string
  student_name: string
  assignment_slug?: string
  assignment_title: string
  final_score: number
  max_score: number
  completed_at: string
}

export interface MentorSubmission {
  id: string
  student_id: string
  student_name: string
  student_roll: string
  assignment_id: string
  assignment_title: string
  assignment_slug: string
  status: SubmissionStatus
  source_type: SubmissionSourceType
  attempt_number: number
  score?: number | null
  max_score?: number | null
  passed?: boolean | null
  submitted_at: string
  started_at?: string | null
  completed_at?: string | null
}

export interface MentorAnalytics {
  total_students: number
  approved_students?: number
  pending_students?: number
  total_sessions?: number
  completed_sessions?: number
  avg_score?: number
  completion_rate?: number
  total_submissions?: number
  score_distribution?: Record<string, number>
  assignments_participation?: Record<string, number>
  category_breakdown?: Record<string, number>
}

export interface Classroom {
  id: string
  name: string
  class_code: string
  mentor_id: string
  created_at: string
}

export interface ClassroomStudentEnrollment {
  enrollment_id: string
  student_id: string
  student_name: string
  student_email: string
  student_roll: string
  classroom_id: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  joined_at: string
}

export interface MentorLoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  role: string
  subject_id?: string
  username?: string
  mentor_uuid?: string
  expires_in?: number
}

// ─── Admin-scoped types ────────────────────────────────────────────
export interface AdminStudent {
  id: string
  roll_number: string
  full_name: string
  email: string
  is_active: boolean
  created_at: string
}

export interface AdminMentor {
  id: string
  username: string
  full_name: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export interface GradingSession {
  id: string
  student_id: string
  student_name: string
  student_roll: string
  assignment_id: string
  assignment_title: string
  assignment_slug: string
  status: string
  started_at: string
  submitted_at?: string
  completed_at?: string
  final_score?: number
  rejection_reason?: string
}

export interface AdminSubmission {
  id: string
  student_id: string
  student_name: string
  student_roll: string
  assignment_id: string
  assignment_title: string
  assignment_slug: string
  status: SubmissionStatus
  source_type: SubmissionSourceType
  attempt_number: number
  score?: number | null
  max_score?: number | null
  passed?: boolean | null
  submitted_at: string
  started_at?: string | null
  completed_at?: string | null
}

export interface HealthResponse {
  status: string
  database: string
  version?: string
}

// ─── Error ─────────────────────────────────────────────────────────
export interface ErrorResponse {
  detail: string | { msg: string; loc: string[] }[]
}
