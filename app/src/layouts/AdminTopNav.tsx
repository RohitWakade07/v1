import { Bell, LogOut } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import { ThemeToggle } from '@/components/shared/ThemeToggle'

export const AdminTopNav = () => {
  const { username, logout } = useAuthStore()
  const notifications = useNotificationStore((s) => s.notifications)
  const location = useLocation()
  const navigate = useNavigate()

  const pathParts = location.pathname.split('/').filter(Boolean)
  const breadcrumb = pathParts.length > 1
    ? pathParts[1].charAt(0).toUpperCase() + pathParts[1].slice(1)
    : 'Dashboard'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-navy-800 bg-navy-950 px-6">
      <div className="flex items-center gap-3">
        <h2 className="font-display text-base font-semibold text-text-primary">{breadcrumb}</h2>
        <span className="rounded-full bg-accent-teal/10 text-accent-teal border border-accent-teal/20 px-3 py-1 text-xs font-bold tracking-wider uppercase">
          Admin
        </span>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative rounded-full p-2 text-text-secondary transition-colors hover:bg-navy-900 hover:text-text-primary">
          <Bell size={18} />
          {notifications.length > 0 && (
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-accent-blue ring-2 ring-navy-950" />
          )}
        </button>
        <ThemeToggle />
        <div className="h-6 w-px bg-navy-800" />
        <span className="text-sm font-medium text-text-primary hidden sm:block">{username || 'Admin'}</span>
        <button
          onClick={handleLogout}
          className="flex h-9 w-9 items-center justify-center rounded-full text-text-secondary transition-colors hover:bg-status-danger/10 hover:text-status-danger"
          title="Log out"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  )
}
