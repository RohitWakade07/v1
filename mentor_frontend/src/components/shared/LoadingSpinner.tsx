import { Loader2 } from 'lucide-react'

export const LoadingSpinner = () => (
  <div className="flex min-h-[200px] items-center justify-center">
    <Loader2 size={28} className="animate-spin text-accent-blue" />
  </div>
)
