import { useMutation } from '@tanstack/react-query'
import { loginMentor } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import { useNavigate } from 'react-router-dom'
import type { MentorLoginRequest } from '@/types/api'

export function useAuth() {
  const login = useAuthStore((s) => s.login)
  const addNotification = useNotificationStore((s) => s.addNotification)
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (credentials: MentorLoginRequest) => loginMentor(credentials),
    onSuccess: (data, variables) => {
      login(
        data.access_token,
        data.role,
        data.subject_id,
        variables.username, // Using passed username as we don't have an explicit endpoint for profile yet
        data.subject_id // mentorUuid typically matches subject_id in our simplified JWT mapping
      )
      addNotification({
        type: 'success',
        title: 'Login successful',
        message: 'Welcome to the Mentor Portal.',
      })
      navigate('/dashboard')
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Login failed',
        message: 'Invalid username or password. Please try again.',
      })
    },
  })
}
