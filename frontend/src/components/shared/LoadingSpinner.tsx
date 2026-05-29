import { Loader2 } from 'lucide-react'

export const LoadingSpinner = () => (
  <div className="flex items-center justify-center gap-2 text-text-secondary">
    <Loader2 className="animate-spin" size={18} />
    <span className="text-sm">Loading...</span>
  </div>
)
