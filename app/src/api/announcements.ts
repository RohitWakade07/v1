import { apiClient } from '@/api/client'

export interface AnnouncementPublic {
  id: string
  admin_id: string
  title: string
  body: string
  audience: 'students' | 'mentors' | 'all'
  expires_at: string | null
  created_at: string
  updated_at: string
  is_read: boolean
}

export interface NotificationPublic {
  id: string
  recipient_id: string
  recipient_type: 'student' | 'mentor'
  source_type: 'announcement' | 'submission' | 'quiz' | 'system'
  source_id: string | null
  title: string
  message: string
  is_read: boolean
  created_at: string
}

// Student
export const getStudentAnnouncements = async () => {
  const { data } = await apiClient.get<AnnouncementPublic[]>('/student/announcements')
  return data
}

export const markAnnouncementReadStudent = async (id: string) => {
  const { data } = await apiClient.post(`/student/announcements/${id}/read`)
  return data
}

export const getStudentNotifications = async () => {
  const { data } = await apiClient.get<NotificationPublic[]>('/student/notifications')
  return data
}

export const markNotificationReadStudent = async (id: string) => {
  const { data } = await apiClient.post(`/student/notifications/${id}/read`)
  return data
}

export const markAllNotificationsReadStudent = async () => {
  const { data } = await apiClient.post('/student/notifications/read-all')
  return data
}

// Mentor
export const getMentorAnnouncements = async () => {
  const { data } = await apiClient.get<AnnouncementPublic[]>('/mentor/announcements')
  return data
}

export const markAnnouncementReadMentor = async (id: string) => {
  const { data } = await apiClient.post(`/mentor/announcements/${id}/read`)
  return data
}

export const getMentorNotifications = async () => {
  const { data } = await apiClient.get<NotificationPublic[]>('/mentor/notifications')
  return data
}

export const markNotificationReadMentor = async (id: string) => {
  const { data } = await apiClient.post(`/mentor/notifications/${id}/read`)
  return data
}

// Admin
export const getAdminAnnouncements = async () => {
  const { data } = await apiClient.get<AnnouncementPublic[]>('/admin/announcements')
  return data
}

export const createAnnouncement = async (payload: { title: string; body: string; audience: string; expires_at?: string }) => {
  const { data } = await apiClient.post<AnnouncementPublic>('/admin/announcements', payload)
  return data
}

export const updateAnnouncement = async (id: string, payload: Partial<{ title: string; body: string; audience: string; expires_at: string }>) => {
  const { data } = await apiClient.patch<AnnouncementPublic>(`/admin/announcements/${id}`, payload)
  return data
}

export const deleteAnnouncement = async (id: string) => {
  await apiClient.delete(`/admin/announcements/${id}`)
}
