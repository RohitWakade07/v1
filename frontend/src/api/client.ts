import axios from 'axios'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status as number | undefined
    const notifier = useNotificationStore.getState()
    if (status === 401) {
      notifier.addNotification({
        type: 'warning',
        title: 'Session expired',
        message: 'Please log in again to continue.',
      })
      useAuthStore.getState().logout()
      const current = `${window.location.pathname}${window.location.search}`
      if (!current.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(current)}`
      }
    } else if (status === 429) {
      notifier.addNotification({
        type: 'warning',
        title: 'Too many attempts',
        message: 'Please wait 60 seconds and try again.',
      })
    } else if (status) {
      notifier.addNotification({
        type: 'error',
        title: 'Request failed',
        message: 'We could not complete that request. Please try again.',
      })
    } else {
      notifier.addNotification({
        type: 'error',
        title: 'Network error',
        message: 'Unable to reach the server. Check your connection.',
      })
    }
    return Promise.reject(error)
  },
)
