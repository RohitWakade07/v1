type StatusVariant = 'active' | 'inactive' | 'published' | 'draft' | 'completed' | 'rejected' | 'submitted' | 'started' | 'in_progress'

const VARIANT: Record<StatusVariant, string> = {
  active:      'bg-accent-teal/10 text-accent-teal border border-accent-teal/20',
  inactive:    'bg-status-warning/10 text-status-warning border border-status-warning/20',
  published:   'bg-accent-teal/10 text-accent-teal border border-accent-teal/20',
  draft:       'bg-status-warning/10 text-status-warning border border-status-warning/20',
  completed:   'bg-accent-teal/10 text-accent-teal border border-accent-teal/20',
  rejected:    'bg-status-danger/10 text-status-danger border border-status-danger/20',
  submitted:   'bg-accent-blue/10 text-accent-blue border border-accent-blue/20',
  started:     'bg-navy-800 text-text-secondary border border-navy-800',
  in_progress: 'bg-accent-blue/10 text-accent-blue border border-accent-blue/20',
}

interface StatusBadgeProps {
  status: string
}

export const StatusBadge = ({ status }: StatusBadgeProps) => {
  const key = status.toLowerCase().replace(' ', '_') as StatusVariant
  const cls = VARIANT[key] ?? 'bg-navy-800 text-text-secondary border border-navy-800'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${cls}`}>
      {status}
    </span>
  )
}
