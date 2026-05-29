import type { ReactNode } from 'react'

interface StatCardProps {
  title: string
  value: string | number
  icon: ReactNode
  subtitle?: string
}

export const StatCard = ({ title, value, icon, subtitle }: StatCardProps) => (
  <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
    <div className="flex items-center justify-between">
      <p className="text-xs uppercase text-text-secondary">{title}</p>
      <div className="text-accent-blue">{icon}</div>
    </div>
    <p className="mt-3 font-display text-3xl font-semibold text-text-primary">
      {value}
    </p>
    {subtitle && <p className="text-xs text-text-secondary">{subtitle}</p>}
  </div>
)
