import { cn } from '@/lib/utils'

interface SkeletonProps {
  className?: string
}

export const Skeleton = ({ className }: SkeletonProps) => (
  <div className={cn('skeleton', className)} />
)

interface SkeletonCardProps {
  rows?: number
  showHeader?: boolean
  className?: string
}

export const SkeletonCard = ({ rows = 3, showHeader = true, className }: SkeletonCardProps) => (
  <div className={cn('rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card', className)}>
    {showHeader && (
      <div className="mb-4 flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
    )}
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className={cn('h-3', i === 0 ? 'w-full' : i === 1 ? 'w-4/5' : 'w-3/5')} />
      ))}
    </div>
  </div>
)

export const SkeletonStatCard = () => (
  <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
    <div className="flex items-center justify-between">
      <Skeleton className="h-3 w-28" />
      <Skeleton className="h-8 w-8 rounded-lg" />
    </div>
    <Skeleton className="mt-4 h-8 w-20" />
    <Skeleton className="mt-2 h-3 w-24" />
  </div>
)

export const SkeletonTableRow = () => (
  <tr className="border-t border-navy-800">
    {Array.from({ length: 5 }).map((_, i) => (
      <td key={i} className="px-4 py-3">
        <Skeleton className="h-3 w-full" />
      </td>
    ))}
  </tr>
)
