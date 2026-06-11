import { GraduationCap, FileCheck2, Trophy, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

const actions = [
  {
    label: 'Browse Assignments',
    description: 'Find and start new evaluations',
    to: '/student/assignments',
    icon: GraduationCap,
    accent: 'bg-accent-blue/15 text-accent-blue',
  },
  {
    label: 'Submit Proof',
    description: 'Upload proof file on assignment page',
    to: '/student/assignments',
    icon: FileCheck2,
    accent: 'bg-accent-teal/15 text-accent-teal',
  },
  {
    label: 'View Results',
    description: 'View scores on assignment details page',
    to: '/student/assignments',
    icon: Trophy,
    accent: 'bg-status-warning/15 text-status-warning',
  },
]

export const QuickActionsPanel = () => (
  <div className="card-dark p-5">
    <h3 className="font-display text-base font-semibold text-text-primary mb-4">Quick Actions</h3>
    <div className="space-y-2">
      {actions.map(({ label, description, to, icon: Icon, accent }) => (
        <Link
          key={label}
          to={to}
          className="group flex items-center gap-3 rounded-lg border border-navy-800 p-3 transition-all hover:border-accent-blue/40 hover:bg-navy-800/40"
        >
          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${accent}`}>
            <Icon size={16} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-text-primary">{label}</p>
            <p className="text-xs text-text-secondary">{description}</p>
          </div>
          <ArrowRight size={14} className="shrink-0 text-text-secondary transition-transform group-hover:translate-x-0.5 group-hover:text-accent-blue" />
        </Link>
      ))}
    </div>
  </div>
)
