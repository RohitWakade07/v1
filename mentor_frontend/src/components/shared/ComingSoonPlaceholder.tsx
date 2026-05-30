import type { LucideIcon } from 'lucide-react'

interface ComingSoonPlaceholderProps {
  icon: LucideIcon
  title: string
  description: string
  phase?: string
  capabilities?: string[]
}

export const ComingSoonPlaceholder = ({
  icon: Icon,
  title,
  description,
  phase = 'Phase 2',
  capabilities,
}: ComingSoonPlaceholderProps) => {
  return (
    <div className="flex min-h-[400px] w-full flex-col items-center justify-center rounded-xl border border-[#253545] bg-[#1A2D42]/50 p-8 text-center animate-fade-in">
      <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-navy-950 shadow-inner">
        <Icon size={64} className="text-[#8CA0B3]" strokeWidth={1.5} />
      </div>
      
      <div className="mb-3 inline-flex items-center rounded-full border border-status-warning/30 bg-status-warning/10 px-3 py-1">
        <span className="text-xs font-semibold uppercase tracking-wider text-status-warning">
          Planned for {phase}
        </span>
      </div>
      
      <h2 className="mb-2 font-display text-2xl font-bold text-text-primary">{title}</h2>
      <p className="mx-auto mb-8 max-w-lg font-body text-text-secondary">{description}</p>
      
      {capabilities && capabilities.length > 0 && (
        <div className="w-full max-w-md rounded-lg border border-[#253545] bg-[#0F1923] p-5 text-left">
          <h3 className="mb-3 font-display text-sm font-semibold text-text-primary">Planned Capabilities</h3>
          <ul className="space-y-2">
            {capabilities.map((cap, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-blue" />
                <span>{cap}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
