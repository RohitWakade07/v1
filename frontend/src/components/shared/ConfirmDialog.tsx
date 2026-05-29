import type { ReactNode } from 'react'

interface ConfirmDialogProps {
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
  isOpen: boolean
  footer?: ReactNode
}

export const ConfirmDialog = ({
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  isOpen,
  footer,
}: ConfirmDialogProps) => {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-xl border border-navy-800 bg-navy-950 p-6 shadow-card">
        <h3 className="font-display text-lg font-semibold text-text-primary">
          {title}
        </h3>
        <p className="mt-2 text-sm text-text-secondary">{message}</p>
        {footer}
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            className="rounded-lg border border-navy-800 px-4 py-2 text-sm text-text-secondary"
            onClick={onCancel}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className="rounded-lg bg-accent-blue px-4 py-2 text-sm font-medium text-white"
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
