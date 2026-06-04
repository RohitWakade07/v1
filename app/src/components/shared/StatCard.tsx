type Accent = 'blue' | 'teal' | 'warning' | 'danger'

const ACCENT_CLASSES: Record<Accent, { icon: string; value: string; border: string }> = {
  blue:    { icon: 'bg-accent-blue/15 text-accent-blue', value: 'text-accent-blue', border: 'border-accent-blue/20' },
  teal:    { icon: 'bg-accent-teal/15 text-accent-teal', value: 'text-accent-teal', border: 'border-accent-teal/20' },
  warning: { icon: 'bg-status-warning/15 text-status-warning', value: 'text-status-warning', border: 'border-status-warning/20' },
  danger:  { icon: 'bg-status-danger/15 text-status-danger', value: 'text-status-danger', border: 'border-status-danger/20' },
}

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  accent?: Accent
  subtitle?: string
}

export const StatCard = ({ title, value, icon, accent = 'blue', subtitle }: StatCardProps) => {
  const cls = ACCENT_CLASSES[accent]
  return (
    <div className={`card-dark p-5 border ${cls.border} transition-card`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold tracking-widest text-text-secondary uppercase">{title}</p>
          <p className={`mt-2 font-display text-3xl font-bold ${cls.value}`}>{value}</p>
          {subtitle && <p className="mt-1 text-xs text-text-secondary">{subtitle}</p>}
        </div>
        <div className={`rounded-xl p-3 ${cls.icon}`}>{icon}</div>
      </div>
    </div>
  )
}
