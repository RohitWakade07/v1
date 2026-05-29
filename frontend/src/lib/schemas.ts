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
  session_id: z.string(),
  assignment_id: z.string(),
  student_id: z.string(),
  timestamp: z.string(),
  nonce: z.string(),
  grader_binary_hash: z.string(),
  results: z.record(
    z.string(),
    z.object({
      passed: z.boolean(),
      score: z.number(),
      stdout_hash: z.string().nullable().optional(),
    }),
  ),
  artifact_hashes: z.record(z.string(), z.string()),
  hmac_signature: z.string(),
})
