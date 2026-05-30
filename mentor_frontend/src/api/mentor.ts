import { apiGet } from './client'
import type { MentorStudent, MentorSession, MentorResult, MentorAnalytics } from '@/types/api'

export async function fetchMentorStudents(): Promise<MentorStudent[]> {
  return apiGet<MentorStudent[]>('/mentor/students')
}

export async function fetchMentorSessions(): Promise<MentorSession[]> {
  return apiGet<MentorSession[]>('/mentor/sessions')
}

export async function fetchMentorResults(): Promise<MentorResult[]> {
  return apiGet<MentorResult[]>('/mentor/results')
}

export async function fetchMentorAnalytics(): Promise<MentorAnalytics> {
  return apiGet<MentorAnalytics>('/mentor/analytics/summary')
}
