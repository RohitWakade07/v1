import { NavLink, useNavigate } from 'react-router-dom'
import {
  GraduationCap, FlaskConical, User, LayoutDashboard, LogOut,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'

const navItems = [
  { label: 'Dashboard',    to: '/student',              icon: LayoutDashboard, end: true },
  { label: 'Assignments',  to: '/student/assignments',  icon: GraduationCap },
  { label: 'Sessions',     to: '/student/sessions',     icon: FlaskConical },
  { label: 'Profile',      to: '/student/profile',      icon: User },
]

export const StudentSidebar = () => {
  const profile = useAuthStore((s) => s.profile)
  const logout = useAuthStore((s) => s.logout)
  const addNotification = useNotificationStore((s) => s.addNotification)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    addNotification({ type: 'info', title: 'Signed out', message: 'See you next time!' })
    navigate('/login')
  }

  const initials = profile?.roll_number?.slice(0, 2).toUpperCase() ?? 'ST'

  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-navy-800 bg-sidebar-bg">
      <div className="flex items-center gap-3 border-b border-navy-800 px-5 py-5">
        <img src="/logo.png" alt="Logo" className="h-9 w-9 object-contain rounded-lg" />
        <div>
          <p className="font-display text-sm font-bold text-text-primary leading-none">E-Yantra EEP</p>
          <p className="text-[10px] text-text-secondary mt-0.5">Student Portal</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-4" aria-label="Student navigation">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              aria-label={item.label}
              className={({ isActive }) =>
                cn(
                  'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-accent-blue/15 text-text-primary'
                    : 'text-text-secondary hover:bg-navy-800/50 hover:text-text-primary',
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r-full bg-accent-blue" />
                  )}
                  <Icon size={16} className={cn(isActive ? 'text-accent-blue' : 'text-text-secondary group-hover:text-text-primary')} />
                  {item.label}
                </>
              )}
            </NavLink>
          )
        })}
      </nav>

      <div className="border-t border-navy-800 px-3 py-4">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-accent-blue to-accent-teal text-xs font-bold text-white">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-text-primary">
              {profile?.full_name ?? profile?.roll_number ?? 'Student'}
            </p>
            <p className="truncate text-[10px] text-text-secondary">{profile?.roll_number}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          aria-label="Sign out"
          className="mt-2 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-text-secondary transition-colors hover:bg-status-danger/10 hover:text-status-danger"
        >
          <LogOut size={15} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
