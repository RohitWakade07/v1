import axios from 'axios'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import type { ErrorResponse } from '@/types/api'

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
    if (!config.headers) {
      config.headers = new axios.AxiosHeaders()
    }
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status as number | undefined
    const notifier = useNotificationStore.getState()
    const errorData = error?.response?.data as ErrorResponse | undefined
    const detail = errorData?.detail

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
    } else if (status === 403) {
      // 403 handling is typically done in components or inline, but we can also toast it here
      notifier.addNotification({
        type: 'error',
        title: 'Permission Denied',
        message: detail || "You don't have permission to perform this action.",
      })
    } else if (status === 429) {
      notifier.addNotification({
        type: 'warning',
        title: 'Too many requests',
        message: 'Please wait before retrying.',
      })
    } else if (status === 409 || status === 422) {
      // Typically handled inline by React Hook Form, but optionally toasted:
      if (status === 409 && detail) {
        notifier.addNotification({ type: 'warning', title: 'Conflict', message: detail })
      }
    } else if (status) {
      notifier.addNotification({
        type: 'error',
        title: 'Request failed',
        message: detail || 'We could not complete that request. Please try again.',
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

export async function apiGet<T>(url: string, params?: Record<string, string | number | boolean>): Promise<T> {
  const { data } = await apiClient.get<T>(url, { params })
  return data
}

export async function apiPost<T, D = unknown>(url: string, data?: D): Promise<T> {
  const { data: responseData } = await apiClient.post<T>(url, data)
  return responseData
}

export async function apiPatch<T, D = unknown>(url: string, data?: D): Promise<T> {
  const { data: responseData } = await apiClient.patch<T>(url, data)
  return responseData
}

export async function apiDelete<T>(url: string): Promise<T> {
  const { data } = await apiClient.delete<T>(url)
  return data
}
