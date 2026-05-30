export const formatDate = (iso: string | undefined | null): string => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export const formatDateTime = (iso: string | undefined | null): string => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export const shortId = (id: string): string => id?.slice(0, 8) ?? '—'

export const greeting = (): string => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export const cn = (...classes: (string | undefined | false | null)[]): string =>
  classes.filter(Boolean).join(' ')
