import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs))

export const formatDate = (value?: string | null): string => {
  if (!value) return 'N/A'
  const date = new Date(value + (value.endsWith('Z') ? '' : 'Z'))
  return new Intl.DateTimeFormat('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export const formatDateTime = (iso: string | undefined | null): string => {
  if (!iso) return '—'
  const d = new Date(iso + (iso.endsWith('Z') ? '' : 'Z'))
  return d.toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export const formatRelative = (value?: string | null): string => {
  if (!value) return 'N/A'
  const date = new Date(value + (value.endsWith('Z') ? '' : 'Z'))
  const diffMs = date.getTime() - Date.now()
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
  const minutes = Math.round(diffMs / 60000)
  if (Math.abs(minutes) < 60) return rtf.format(minutes, 'minute')
  const hours = Math.round(diffMs / 3600000)
  if (Math.abs(hours) < 24) return rtf.format(hours, 'hour')
  const days = Math.round(diffMs / 86400000)
  return rtf.format(days, 'day')
}

export const formatScore = (score?: number | null, max?: number | null): string => {
  if (score === null || score === undefined) return 'N/A'
  if (!max) return score.toFixed(1)
  return `${score.toFixed(1)} / ${max.toFixed(1)}`
}

export const truncateHash = (value?: string | null, head = 6, tail = 6): string => {
  if (!value) return 'N/A'
  if (value.length <= head + tail) return value
  return `${value.slice(0, head)}...${value.slice(-tail)}`
}

export const shortId = (id: string | undefined | null): string => id?.slice(0, 8) ?? '—'

export const greeting = (): string => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

/** Decode JWT exp claim without a library and check if expired.
 *  Subtracts a 30-second buffer so we don't use a token that will
 *  expire mid-request during a slow network call. */
export const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp * 1000 < Date.now() + 30_000
  } catch {
    return true // Malformed token — treat as expired
  }
}
