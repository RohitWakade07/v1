import { ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PaginationProps {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
  className?: string
}

export const Pagination = ({ page, totalPages, onPageChange, className }: PaginationProps) => {
  if (totalPages <= 1) return null

  const getVisiblePages = () => {
    const delta = 2
    const range = []
    for (
      let i = Math.max(2, page - delta);
      i <= Math.min(totalPages - 1, page + delta);
      i++
    ) {
      range.push(i)
    }

    if (page - delta > 2) {
      range.unshift('...')
    }
    if (page + delta < totalPages - 1) {
      range.push('...')
    }

    range.unshift(1)
    if (totalPages > 1) {
      range.push(totalPages)
    }

    return range
  }

  const pages = getVisiblePages()

  return (
    <div className={cn("flex items-center justify-center gap-2 py-4", className)}>
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
        className="flex h-8 w-8 items-center justify-center rounded-md border border-navy-700 bg-navy-900 text-text-secondary transition-colors hover:bg-navy-800 disabled:opacity-50 disabled:hover:bg-navy-900"
      >
        <ChevronLeft size={16} />
      </button>

      {pages.map((p, idx) =>
        p === '...' ? (
          <span key={idx} className="flex h-8 w-8 items-center justify-center text-text-secondary">
            <MoreHorizontal size={16} />
          </span>
        ) : (
          <button
            key={idx}
            onClick={() => onPageChange(p as number)}
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-md border transition-colors text-sm font-medium",
              page === p
                ? "border-accent-blue bg-accent-blue/10 text-accent-blue"
                : "border-navy-700 bg-navy-900 text-text-secondary hover:bg-navy-800 hover:text-text-primary"
            )}
          >
            {p}
          </button>
        )
      )}

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        className="flex h-8 w-8 items-center justify-center rounded-md border border-navy-700 bg-navy-900 text-text-secondary transition-colors hover:bg-navy-800 disabled:opacity-50 disabled:hover:bg-navy-900"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  )
}
