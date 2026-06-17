import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getStudentNotifications, markNotificationReadStudent, markAllNotificationsReadStudent, getMentorNotifications, markNotificationReadMentor, NotificationPublic } from '@/api/announcements'
import { useAuthStore } from '@/store/authStore'

export const useNotifications = () => {
  const role = useAuthStore(s => s.role)
  
  return useQuery({
    queryKey: ['notifications', role],
    queryFn: async (): Promise<NotificationPublic[]> => {
      if (role === 'student') {
        return getStudentNotifications()
      } else if (role === 'mentor') {
        return getMentorNotifications()
      }
      return []
    },
    enabled: role === 'student' || role === 'mentor',
    refetchInterval: 30000, // refresh every 30s
  })
}

export const useMarkNotificationRead = () => {
  const queryClient = useQueryClient()
  const role = useAuthStore(s => s.role)

  return useMutation({
    mutationFn: async (id: string) => {
      if (role === 'student') return markNotificationReadStudent(id)
      if (role === 'mentor') return markNotificationReadMentor(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    }
  })
}

export const useMarkAllNotificationsRead = () => {
  const queryClient = useQueryClient()
  const role = useAuthStore(s => s.role)

  return useMutation({
    mutationFn: async () => {
      if (role === 'student') return markAllNotificationsReadStudent()
      // mentor doesn't have read-all implemented in API yet, but we can just resolve
      if (role === 'mentor') return Promise.resolve()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    }
  })
}
