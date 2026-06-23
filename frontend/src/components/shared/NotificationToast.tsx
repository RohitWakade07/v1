import { useEffect, useRef } from 'react'
import { X, CheckCircle2, XCircle, AlertTriangle, Info } from 'lucide-react'
import { useNotificationStore } from '@/store/notificationStore'
import { cn } from '@/lib/utils'

const icons = { success: CheckCircle2, error: XCircle, warning: AlertTriangle, info: Info }
const styles = {
  success: 'border-accent-teal/40 text-accent-teal',
  error:   'border-status-danger/40 text-status-danger',
  warning: 'border-status-warning/40 text-status-warning',
  info:    'border-accent-blue/40 text-accent-blue',
}
const barColors = {
  success: 'bg-accent-teal', error: 'bg-status-danger',
  warning: 'bg-status-warning', info: 'bg-accent-blue',
}

const AUTO_DISMISS_MS = 4000

const ToastItem = ({ id, type, title, message }: {
  id: string; type: keyof typeof icons; title: string; message: string
}) => {
  const remove = useNotificationStore((s) => s.removeNotification)
  const barRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const timer = setTimeout(() => remove(id), AUTO_DISMISS_MS)
    if (barRef.current) {
      barRef.current.style.animation = `progressBar ${AUTO_DISMISS_MS}ms linear forwards`
    }
    return () => clearTimeout(timer)
  }, [id, remove])

  const Icon = icons[type]
  return (
    <div
      className={cn('animate-slide-in-right relative overflow-hidden rounded-xl border bg-navy-900 px-4 py-3 shadow-card', styles[type])}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-start gap-3">
        <Icon size={18} className="mt-0.5 shrink-0" />
        <div className="flex-1 pr-6">
          <p className="text-sm font-semibold text-text-primary">{title}</p>
          <p className="mt-0.5 text-xs text-text-secondary">{message}</p>
        </div>
        <button
          aria-label="Dismiss notification"
          onClick={() => remove(id)}
          className="absolute right-3 top-3 text-text-secondary hover:text-text-primary transition-colors"
        >
          <X size={14} />
        </button>
      </div>
      <div className="absolute bottom-0 left-0 h-0.5 w-full bg-navy-800">
        <div ref={barRef} className={cn('h-full', barColors[type])} style={{ width: '100%' }} />
      </div>
    </div>
  )
}

export const NotificationToast = () => {
  const notifications = useNotificationStore((s) => s.notifications)
  return (
    <div className="fixed right-4 top-4 z-50 flex w-80 flex-col gap-2" aria-label="Notifications">
      {notifications.map((note) => <ToastItem key={note.id} {...note} />)}
    </div>
  )
}
