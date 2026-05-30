import { z } from 'zod'

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
