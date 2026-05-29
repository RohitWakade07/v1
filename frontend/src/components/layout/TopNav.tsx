import { Bell, Search } from 'lucide-react'
import { useNotificationStore } from '@/store/notificationStore'

interface TopNavProps {
  title: string
}

export const TopNav = ({ title }: TopNavProps) => {
  const count = useNotificationStore((state) => state.notifications.length)

  return (
    <header className="flex items-center justify-between border-b border-navy-800 bg-navy-950 px-8 py-5">
      <div>
        <h2 className="font-display text-2xl font-semibold text-text-primary">
          {title}
        </h2>
        <p className="text-sm text-text-secondary">
          Secure Academic Grading Platform
        </p>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-lg border border-navy-800 bg-navy-900 px-3 py-2 text-sm text-text-secondary">
          <Search size={16} />
          <span>Search...</span>
        </div>
        <div className="relative">
          <Bell className="text-text-secondary" size={20} />
          {count > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-accent-blue text-[10px] text-white">
              {count > 9 ? '9+' : count}
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
