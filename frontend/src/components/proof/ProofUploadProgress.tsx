import { Loader2, CheckCircle2, XCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ProofUploadProgressProps {
  status: 'idle' | 'uploading' | 'success' | 'error'
  message?: string
}

export const ProofUploadProgress = ({ status, message }: ProofUploadProgressProps) => {
  if (status === 'idle') return null

  const config = {
    uploading: {
      icon: <Loader2 size={16} className="animate-spin" />,
      style: 'border-accent-blue/30 bg-accent-blue/10 text-accent-blue',
    },
    success: {
      icon: <CheckCircle2 size={16} />,
      style: 'border-accent-teal/30 bg-accent-teal/10 text-accent-teal',
    },
    error: {
      icon: <XCircle size={16} />,
      style: 'border-status-danger/30 bg-status-danger/10 text-status-danger',
    },
  }[status] ?? {
    icon: <Info size={16} />,
    style: 'border-navy-800 bg-navy-900 text-text-secondary',
  }

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg border px-4 py-3 text-sm animate-fade-in',
        config.style,
      )}
      role="status"
      aria-live="polite"
    >
      {config.icon}
      <span>{message}</span>
    </div>
  )
}
