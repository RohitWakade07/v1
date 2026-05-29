import { NavLink } from 'react-router-dom'
import {
  GraduationCap,
  FlaskConical,
  FileCheck2,
  Trophy,
  User,
  LayoutDashboard,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { label: 'Dashboard', to: '/', icon: LayoutDashboard },
  { label: 'Assignments', to: '/assignments', icon: GraduationCap },
  { label: 'Sessions', to: '/sessions', icon: FlaskConical },
  { label: 'Submit Proof', to: '/proof/submit', icon: FileCheck2 },
  { label: 'Results', to: '/results', icon: Trophy },
  { label: 'Profile', to: '/profile', icon: User },
]

export const Sidebar = () => {
  return (
    <aside className="sticky top-0 flex h-screen w-60 flex-col border-r border-navy-800 bg-navy-950 px-6 py-8">
      <div className="mb-10">
        <h1 className="font-display text-xl font-bold text-text-primary">
          Secure Grading
        </h1>
        <p className="text-sm text-text-secondary">Student Portal</p>
      </div>
      <nav className="flex flex-1 flex-col gap-2">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-text-secondary transition',
                  isActive
                    ? 'bg-navy-900 text-text-primary'
                    : 'hover:bg-navy-900/60 hover:text-text-primary',
                )
              }
            >
              <Icon size={18} />
              {item.label}
            </NavLink>
          )
        })}
      </nav>
      <div className="rounded-lg border border-navy-800 bg-navy-900/40 p-4 text-xs text-text-secondary">
        Version 1.0 - Phase 1
      </div>
    </aside>
  )
}
