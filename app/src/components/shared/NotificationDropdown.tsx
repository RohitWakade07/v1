import { useState, useRef, useEffect } from 'react'
import { Bell, Check, Info, AlertTriangle, AlertCircle, CheckCircle2 } from 'lucide-react'
import { useNotifications, useMarkNotificationRead, useMarkAllNotificationsRead } from '@/hooks/useNotifications'
import { formatDate } from '@/lib/utils'

export const NotificationDropdown = () => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  const { data: rawNotifications, isLoading } = useNotifications()
  const notifications = Array.isArray(rawNotifications) ? rawNotifications : []
  
  const { mutate: markRead } = useMarkNotificationRead()
  const { mutate: markAllRead } = useMarkAllNotificationsRead()

  const unreadCount = notifications.filter(n => !n.is_read).length

  // Handle outside click to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  const getIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'announcement': return <Info size={16} className="text-accent-blue" />
      case 'submission': return <CheckCircle2 size={16} className="text-accent-teal" />
      case 'quiz': return <AlertTriangle size={16} className="text-status-warning" />
      default: return <AlertCircle size={16} className="text-text-secondary" />
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`${unreadCount} unread notifications`}
        className={`relative flex h-9 w-9 items-center justify-center rounded-lg border transition-colors ${
          isOpen ? 'border-accent-blue/40 bg-navy-800 text-text-primary' : 'border-navy-800 bg-navy-900 text-text-secondary hover:text-text-primary'
        }`}
      >
        <Bell size={16} />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-accent-blue text-[9px] font-bold text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-navy-800 bg-navy-950 shadow-xl z-50 animate-fade-in-up">
          <div className="flex items-center justify-between border-b border-navy-800 p-3">
            <h3 className="font-display font-semibold text-text-primary">Notifications</h3>
            {unreadCount > 0 && (
              <button 
                onClick={() => markAllRead()}
                className="text-xs text-accent-blue hover:text-accent-teal transition-colors"
              >
                Mark all as read
              </button>
            )}
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="p-8 text-center text-sm text-text-secondary">Loading...</div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center flex flex-col items-center">
                <Bell size={24} className="text-navy-800 mb-2" />
                <p className="text-sm text-text-secondary">No notifications yet.</p>
              </div>
            ) : (
              <div className="flex flex-col divide-y divide-navy-800">
                {notifications.map((note) => (
                  <div 
                    key={note.id} 
                    className={`flex items-start gap-3 p-3 transition-colors ${!note.is_read ? 'bg-navy-900/50' : 'hover:bg-navy-900/30'}`}
                  >
                    <div className="mt-0.5 shrink-0">
                      {getIcon(note.source_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${!note.is_read ? 'font-medium text-text-primary' : 'text-text-secondary'}`}>
                        {note.title}
                      </p>
                      <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">
                        {note.message}
                      </p>
                      <p className="text-[10px] text-text-secondary mt-1.5 opacity-70">
                        {formatDate(note.created_at)}
                      </p>
                    </div>
                    {!note.is_read && (
                      <button 
                        onClick={() => markRead(note.id)}
                        className="shrink-0 p-1 text-text-secondary hover:text-accent-teal transition-colors"
                        title="Mark as read"
                      >
                        <Check size={14} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="border-t border-navy-800 p-2 text-center">
            <span className="text-[10px] text-text-secondary uppercase tracking-widest">End of notifications</span>
          </div>
        </div>
      )}
    </div>
  )
}
