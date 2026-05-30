import type { ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
  icon?: ReactNode
  variant?: 'default' | 'danger'
}

export const ConfirmDialog = ({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  icon,
  variant = 'default',
}: ConfirmDialogProps) => {
  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />
      {/* Panel */}
      <div className="relative z-10 w-full max-w-sm animate-fade-in-up rounded-xl border border-navy-800 bg-navy-900 p-6 shadow-card">
        <div className="flex items-start gap-4">
          <div
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
              variant === 'danger' ? 'bg-status-danger/15 text-status-danger' : 'bg-accent-blue/15 text-accent-blue'
            }`}
          >
            {icon ?? <AlertTriangle size={20} />}
          </div>
          <div>
            <h3
              id="dialog-title"
              className="font-display text-base font-semibold text-text-primary"
            >
              {title}
            </h3>
            <p className="mt-1 text-sm text-text-secondary">{message}</p>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button className="btn-secondary text-sm px-4 py-2" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button
            className={variant === 'danger' ? 'btn-danger text-sm px-4 py-2' : 'btn-primary text-sm px-4 py-2'}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
