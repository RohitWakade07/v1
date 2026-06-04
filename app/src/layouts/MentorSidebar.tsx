import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, GraduationCap, BookOpen, Users, FlaskConical,
  ClipboardCheck, BarChart3, Cpu, Award, Lock,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { path: '/mentor',             label: 'Dashboard',   icon: LayoutDashboard, end: true },
  { path: '/mentor/classrooms',  label: 'Classrooms',  icon: GraduationCap },
  { path: '/mentor/assignments', label: 'Assignments',  icon: BookOpen },
  { path: '/mentor/students',    label: 'Students',     icon: Users },
  { path: '/mentor/sessions',    label: 'Sessions',     icon: FlaskConical },
  { path: '/mentor/results',     label: 'Results',      icon: ClipboardCheck },
  { path: '/mentor/analytics',   label: 'Analytics',    icon: BarChart3 },
]

const phase2Items = [
  { label: 'Evaluators',    icon: Cpu },
  { label: 'Certificates',  icon: Award },
]

export const MentorSidebar = () => {
  const location = useLocation()

  return (
    <aside className="flex h-full w-[240px] flex-col border-r border-navy-800 bg-sidebar-bg transition-all duration-300">
      <div className="flex h-16 items-center gap-3 bg-navy-900 px-6 border-b border-navy-800">
        <img src="/logo.png" alt="Logo" className="h-6 w-6 object-contain rounded" />
        <span className="font-display text-lg font-bold text-text-primary">Mentor Portal</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-6 space-y-1">
        {navItems.map(({ path, label, icon: Icon, end }) => {
          const isActive = end ? location.pathname === path : location.pathname.startsWith(path)
          return (
            <NavLink
              key={path}
              to={path}
              end={end}
              className={cn(
                'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-navy-900/60 text-accent-blue border-l-4 border-accent-blue'
                  : 'border-l-4 border-transparent text-text-secondary hover:bg-navy-900/40 hover:text-text-primary',
              )}
            >
              <Icon size={18} className={isActive ? 'text-accent-blue' : 'text-text-secondary group-hover:text-text-primary'} />
              {label}
            </NavLink>
          )
        })}

        <div className="mt-8 mb-4 px-4 text-xs font-semibold uppercase tracking-wider text-text-secondary/60">
          Phase 2
        </div>
        {phase2Items.map(({ label, icon: Icon }) => (
          <div
            key={label}
            title="Coming in Phase 2"
            className="group flex cursor-not-allowed items-center justify-between rounded-lg px-4 py-2.5 text-sm font-medium text-text-secondary/50 opacity-60 border-l-4 border-transparent"
          >
            <div className="flex items-center gap-3">
              <Icon size={18} />
              {label}
            </div>
            <Lock size={14} className="text-text-secondary/40" />
          </div>
        ))}
      </nav>

      <div className="border-t border-navy-800 p-4 flex items-center justify-center">
        <span className="text-xs text-text-secondary">Platform Management</span>
      </div>
    </aside>
  )
}
