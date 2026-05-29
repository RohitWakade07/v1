interface ProofUploadProgressProps {
  status: 'idle' | 'uploading' | 'success' | 'error'
  message?: string
}

export const ProofUploadProgress = ({
  status,
  message,
}: ProofUploadProgressProps) => {
  if (status === 'idle') return null

  const styles: Record<'uploading' | 'success' | 'error', string> = {
    uploading: 'border-accent-blue/40 text-accent-blue',
    success: 'border-accent-teal/40 text-accent-teal',
    error: 'border-status-danger/40 text-status-danger',
  }

  return (
    <div className={`rounded-xl border px-4 py-3 text-sm ${styles[status]}`}>
      {message}
    </div>
  )
}
