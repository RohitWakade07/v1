import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs))

export const formatDate = (value?: string) => {
  if (!value) return 'N/A'
  const date = new Date(value)
  return new Intl.DateTimeFormat('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export const formatRelative = (value?: string) => {
  if (!value) return 'N/A'
  const date = new Date(value)
  const diffMs = date.getTime() - Date.now()
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
  const minutes = Math.round(diffMs / 60000)
  if (Math.abs(minutes) < 60) return rtf.format(minutes, 'minute')
  const hours = Math.round(diffMs / 3600000)
  if (Math.abs(hours) < 24) return rtf.format(hours, 'hour')
  const days = Math.round(diffMs / 86400000)
  return rtf.format(days, 'day')
}

export const formatScore = (score?: number | null, max?: number | null) => {
  if (score === null || score === undefined) return 'N/A'
  if (!max) return score.toFixed(1)
  return `${score.toFixed(1)} / ${max.toFixed(1)}`
}

export const truncateHash = (value?: string, head = 6, tail = 6) => {
  if (!value) return 'N/A'
  if (value.length <= head + tail) return value
  return `${value.slice(0, head)}...${value.slice(-tail)}`
}
