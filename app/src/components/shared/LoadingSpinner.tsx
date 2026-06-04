import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LoadingSpinnerProps { className?: string; size?: number }
export const LoadingSpinner = ({ className, size = 24 }: LoadingSpinnerProps) => (
  <div className={cn('flex items-center justify-center p-8', className)}>
    <Loader2 size={size} className="animate-spin text-accent-blue" />
  </div>
)
