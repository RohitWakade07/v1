import { Bell, ChevronRight } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { useNotificationStore } from '@/store/notificationStore'
import { useAuthStore } from '@/store/authStore'
import { ThemeToggle } from '@/components/shared/ThemeToggle'

const routeLabels: Record<string, string> = {
  '': 'Dashboard',
  assignments: 'Assignments',
  sessions: 'Sessions',
  proof: 'Proof',
  submit: 'Submit',
  results: 'Results',
  profile: 'Profile',
}

const useBreadcrumbs = () => {
  const location = useLocation()
  const segments = location.pathname.split('/').filter(Boolean)
  if (segments.length === 0) return [{ label: 'Dashboard', to: '/' }]
  return segments.map((seg, i) => ({
    label: routeLabels[seg] ?? (seg.length === 36 ? `${seg.slice(0, 8)}…` : seg),
    to: '/' + segments.slice(0, i + 1).join('/'),
  }))
}

export const TopNav = () => {
  const crumbs = useBreadcrumbs()
  const count = useNotificationStore((s) => s.notifications.length)
  const clearAll = useNotificationStore((s) => s.clearNotifications)
  const profile = useAuthStore((s) => s.profile)
  const initials = profile?.roll_number?.slice(0, 2).toUpperCase() ?? 'ST'

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-navy-800 bg-navy-950 px-6">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm">
        {crumbs.map((crumb, i) => (
          <span key={crumb.to} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={14} className="text-text-secondary" />}
            {i === crumbs.length - 1 ? (
              <span className="font-display font-semibold text-text-primary">{crumb.label}</span>
            ) : (
              <Link to={crumb.to} className="text-text-secondary hover:text-text-primary transition-colors">
                {crumb.label}
              </Link>
            )}
          </span>
        ))}
      </nav>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Bell */}
        <button
          aria-label={`${count} notifications`}
          onClick={count > 0 ? clearAll : undefined}
          className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-navy-800 bg-navy-900 text-text-secondary transition-colors hover:text-text-primary"
        >
          <Bell size={16} />
          {count > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-accent-blue text-[9px] font-bold text-white">
              {count > 9 ? '9+' : count}
            </span>
          )}
        </button>

        {/* Theme toggle */}
        <ThemeToggle />

        {/* Avatar */}
        <Link
          to="/profile"
          aria-label="Profile"
          className="flex items-center gap-2 rounded-lg border border-navy-800 bg-navy-900 px-3 py-1.5 transition-colors hover:border-accent-blue/40"
        >
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-accent-blue to-accent-teal text-[10px] font-bold text-white">
            {initials}
          </div>
          <span className="text-xs font-medium text-text-secondary">
            {profile?.roll_number ?? 'Student'}
          </span>
        </Link>
      </div>
    </header>
  )
}
