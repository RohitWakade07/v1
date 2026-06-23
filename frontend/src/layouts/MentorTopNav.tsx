import { LogOut, User, Menu } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { cn } from '@/lib/utils'
import { ThemeToggle } from '@/components/shared/ThemeToggle'
import { NotificationDropdown } from '@/components/shared/NotificationDropdown'

export const MentorTopNav = ({ onMenuClick }: { onMenuClick?: () => void }) => {
  const { role, username, logout } = useAuthStore()
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
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-navy-800 bg-navy-950 px-4 md:px-6">
      <div className="flex items-center gap-3 md:gap-4">
        {onMenuClick && (
          <button onClick={onMenuClick} className="md:hidden text-text-secondary hover:text-text-primary">
            <Menu size={24} />
          </button>
        )}
        <h2 className="text-lg font-medium text-text-primary hidden sm:block">{breadcrumb}</h2>
        {role && (
          <div className={cn(
            'rounded-full px-3 py-1 text-xs font-bold tracking-wider uppercase border',
            role === 'admin'
              ? 'bg-accent-teal/10 text-accent-teal border-accent-teal/20'
              : 'bg-accent-blue/10 text-accent-blue border-accent-blue/20',
          )}>
            {role}
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        <NotificationDropdown />


        <ThemeToggle />
        <div className="h-6 w-px bg-navy-800" />

        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-text-primary hidden sm:block">
            {username || 'Mentor'}
          </span>
          <Link
            to="/mentor/profile"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-navy-900 text-text-secondary transition-colors hover:text-text-primary hover:bg-navy-800"
          >
            <User size={18} />
          </Link>
          <button
            onClick={handleLogout}
            className="flex h-9 w-9 items-center justify-center rounded-full text-text-secondary transition-colors hover:bg-status-danger/10 hover:text-status-danger"
            title="Log out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </header>
  )
}
