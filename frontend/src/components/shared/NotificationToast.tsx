import { useEffect } from 'react'
import { CheckCircle2, XCircle, Bell, AlertTriangle } from 'lucide-react'
import { useNotificationStore } from '@/store/notificationStore'
import { cn } from '@/lib/utils'

const icons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Bell,
}

const styles = {
  success: 'border-accent-teal/40 bg-navy-900 text-accent-teal',
  error: 'border-status-danger/40 bg-navy-900 text-status-danger',
  warning: 'border-status-warning/40 bg-navy-900 text-status-warning',
  info: 'border-accent-blue/40 bg-navy-900 text-accent-blue',
}

export const NotificationToast = () => {
  const { notifications, removeNotification } = useNotificationStore()

  useEffect(() => {
    const timers = notifications.map((note) =>
      setTimeout(() => removeNotification(note.id), 4000),
    )
    return () => timers.forEach((timer) => clearTimeout(timer))
  }, [notifications, removeNotification])

  return (
    <div className="fixed right-6 top-6 z-50 flex w-80 flex-col gap-3">
      {notifications.map((note) => {
        const Icon = icons[note.type]
        return (
          <div
            key={note.id}
            className={cn(
              'flex items-start gap-3 rounded-lg border px-4 py-3 text-sm shadow-card',
              styles[note.type],
            )}
          >
            <Icon size={18} />
            <div className="text-text-primary">
              <p className="font-medium text-text-primary">{note.title}</p>
              <p className="text-xs text-text-secondary">{note.message}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
