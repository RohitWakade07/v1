import { apiPost } from './client'
import type { MentorLoginRequest, TokenResponse } from '@/types/api'

export async function loginMentor(credentials: MentorLoginRequest): Promise<TokenResponse> {
  // Using URLSearchParams or FormData for OAuth2 compatible login endpoints if required,
  // but PRD specifies "POST /auth/mentor/login with { username, password }".
  // Assuming it accepts JSON as per standard endpoints unless it's strict OAuth2 Form Data.
  return apiPost<TokenResponse, MentorLoginRequest>('/auth/mentor/login', credentials)
}
