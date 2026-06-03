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
    const skipToast = error?.config?.headers?.['x-skip-error-toast'] === 'true'

    if (status === 401) {
      if (!skipToast) {
        notifier.addNotification({
          type: 'warning',
          title: 'Session expired',
          message: 'Please log in again to continue.',
        })
      }
      useAuthStore.getState().logout()
      const current = `${window.location.pathname}${window.location.search}`
      if (!current.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(current)}`
      }
    } else if (status === 429) {
      if (!skipToast) {
        notifier.addNotification({
          type: 'warning',
          title: 'Too many attempts',
          message: 'Please wait 60 seconds and try again.',
        })
      }
    } else if (status) {
      if (!skipToast) {
        let message = 'We could not complete that request. Please try again.'
        const detail = error.response?.data?.detail
        if (detail) {
          if (Array.isArray(detail)) {
            message = detail
              .map((err: any) => {
                const field = err.loc && err.loc.length > 0 ? err.loc[err.loc.length - 1] : 'field'
                return `"${field}" ${err.msg}`
              })
              .join(', ')
          } else {
            message = detail
          }
        }
        notifier.addNotification({
          type: 'error',
          title: 'Request failed',
          message,
        })
      }
    } else {
      if (!skipToast) {
        notifier.addNotification({
          type: 'error',
          title: 'Network error',
          message: 'Unable to reach the server. Check your connection.',
        })
      }
    }
    return Promise.reject(error)
  },
)
