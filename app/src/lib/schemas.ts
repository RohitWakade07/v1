import { z } from 'zod'

export const loginSchema = z.object({
  rollNumber: z.string().min(3, 'Roll number is required'),
  password: z.string().min(6, 'Password is required'),
})

export const registerSchema = z.object({
  fullName: z.string().min(2, 'Full name is required'),
  email: z.string().email('Enter a valid email'),
  rollNumber: z.string().min(3, 'Roll number is required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  classCode: z.string().min(1, 'Class code is required'),
})

export const passwordChangeSchema = z
  .object({
    currentPassword: z.string().min(6, 'Current password is required'),
    newPassword: z.string().min(6, 'New password must be at least 6 characters'),
    confirmPassword: z.string().min(6, 'Confirm the new password'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

export const proofFileSchema = z.object({
  session_id: z.string().uuid('Session ID must be a valid UUID'),
  assignment_id: z.string().uuid('Assignment ID must be a valid UUID'),
  student_id: z.string().min(1, 'Student ID (roll number) is required'),
  timestamp: z.string().min(1, 'Timestamp is required'),
  nonce: z.string().uuid('Nonce must be a valid UUID'),
  grader_binary_hash: z.string().min(1, 'Grader binary hash is required'),
  results: z.record(
    z.string(),
    z.object({
      test_id: z.string().min(1, 'Test ID is required'),
      passed: z.boolean('Passed must be a boolean'),
      stdout_hash: z.string().nullable().optional(),
      stderr_hash: z.string().nullable().optional(),
      exit_code: z.number().int('Exit code must be an integer').default(0),
      score: z.number('Score must be a number').default(0.0),
    }),
  ),
  artifact_hashes: z.record(z.string(), z.string()),
  hmac_signature: z.string().min(1, 'HMAC signature is required'),
})

export const createAssignmentSchema = z.object({
  title: z.string().min(3).max(300),
  slug: z.string()
    .min(2).max(100)
    .regex(/^[a-z0-9-]+$/, 'Slug must be lowercase alphanumeric with hyphens only'),
  description: z.string().max(2000).optional(),
  category: z.enum([
    'artifact_validation', 'deterministic_execution', 'filesystem_validation',
    'git_validation', 'network_validation', 'documentation_review', 'manual_review'
  ]),
  max_score: z.number().min(1).max(1000),
  deadline: z.string().optional(),
  publish_immediately: z.boolean(),
})

export const mentorLoginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})
