import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, GraduationCap, BookOpen, Users,
  ClipboardCheck, BarChart3, Inbox, X
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { path: '/mentor',               label: 'Dashboard',        icon: LayoutDashboard, end: true },
  { path: '/mentor/classrooms',    label: 'Classrooms',       icon: GraduationCap },
  { path: '/mentor/assignments',   label: 'Assignments',      icon: BookOpen },
  { path: '/mentor/students',      label: 'Students',         icon: Users },
  { path: '/mentor/submissions',   label: 'Submissions',      icon: Inbox },
  { path: '/mentor/results',       label: 'Results',          icon: ClipboardCheck },
  { path: '/mentor/analytics',     label: 'Analytics',        icon: BarChart3 },
]

export const MentorSidebar = ({ isOpen, onClose }: { isOpen?: boolean, onClose?: () => void }) => {
  const location = useLocation()

  return (
    <aside className={`fixed inset-y-0 left-0 z-50 flex h-full w-[240px] flex-col border-r border-navy-800 bg-sidebar-bg transition-transform duration-300 md:relative md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex h-16 items-center gap-3 bg-navy-900 px-4 md:px-6 border-b border-navy-800">
        <img src="/logo.png" alt="Logo" className="h-6 w-6 object-contain rounded" />
        <span className="font-display text-lg font-bold text-text-primary">Mentor Portal</span>
        {onClose && (
          <button onClick={onClose} className="ml-auto md:hidden text-text-secondary hover:text-text-primary">
            <X size={20} />
          </button>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-6 space-y-1">
        {navItems.map(({ path, label, icon: Icon, end }) => {
          const isActive = end ? location.pathname === path : location.pathname.startsWith(path)
          return (
            <NavLink
              key={path}
              to={path}
              end={end}
              onClick={onClose}
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
      </nav>

      <div className="border-t border-navy-800 p-4 flex items-center justify-center">
        <span className="text-xs text-text-secondary">Platform Management</span>
      </div>
    </aside>
  )
}
