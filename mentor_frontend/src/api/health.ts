import { apiGet } from './client'

export interface HealthStatus {
  status: 'ok' | 'degraded' | 'down'
}

export async function fetchHealth(): Promise<HealthStatus> {
  try {
    const res = await apiGet<{ status: string }>('/health')
    return { status: res.status === 'ok' ? 'ok' : 'degraded' }
  } catch {
    return { status: 'down' }
  }
}
