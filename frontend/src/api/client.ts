import axios, { InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import type { ErrorResponse } from '@/types/api'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: attach JWT ───────────────────────────────
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

// ── Response interceptor: unified error handling ──────────────────
apiClient.interceptors.response.use(
  (res: AxiosResponse) => res,
  (error: any) => {
    const status = error?.response?.status as number | undefined
    const notifier = useNotificationStore.getState()
    const errorData = error?.response?.data as ErrorResponse | undefined
    const skipToast = error?.config?.headers?.['x-skip-error-toast'] === 'true'

    let detail: string | undefined
    if (typeof errorData?.detail === 'string') {
      detail = errorData.detail
    } else if (Array.isArray(errorData?.detail)) {
      detail = errorData.detail
        .map((d) => {
          const field = d.loc?.length ? d.loc[d.loc.length - 1] : 'field'
          return `"${field}" ${d.msg}`
        })
        .join(', ')
    }

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
    } else if (status === 403) {
      if (!skipToast) {
        notifier.addNotification({
          type: 'error',
          title: 'Access denied',
          message: detail ?? "You don't have permission to perform this action.",
        })
      }
    } else if (status === 429) {
      if (!skipToast) {
        notifier.addNotification({
          type: 'warning',
          title: 'Too many requests',
          message: 'Please wait before retrying.',
        })
      }
    } else if (status && !skipToast) {
      notifier.addNotification({
        type: 'error',
        title: 'Request failed',
        message: detail ?? 'We could not complete that request. Please try again.',
      })
    } else if (!status && !skipToast) {
      notifier.addNotification({
        type: 'error',
        title: 'Network error',
        message: 'Unable to reach the server. Check your connection.',
      })
    }

    return Promise.reject(error)
  },
)

// ── Convenience wrappers ──────────────────────────────────────────
export async function apiGet<T>(
  url: string,
  params?: Record<string, string | number | boolean>,
): Promise<T> {
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
