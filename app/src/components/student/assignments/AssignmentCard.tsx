import { ArrowRight, Timer, Award } from 'lucide-react'
import type { AssignmentSummary } from '@/types/api'
import { formatRelative } from '@/lib/utils'
import { CategoryBadge } from '@/components/shared/StatusBadge'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'

const isUrgent = (deadline?: string) => {
  if (!deadline) return false
  return new Date(deadline).getTime() - Date.now() < 48 * 3600 * 1000
}

interface AssignmentCardProps {
  assignment: AssignmentSummary
}

export const AssignmentCard = ({ assignment }: AssignmentCardProps) => {
  const urgent = isUrgent(assignment.deadline)

  return (
    <div className={cn(
      'card-dark transition-card flex flex-col p-5',
      urgent && 'border-status-warning/30',
    )}>
      <div className="flex items-start justify-between gap-2">
        <CategoryBadge category={assignment.category} />
        <span className="flex items-center gap-1 text-xs text-text-secondary shrink-0">
          <Award size={12} />
          {assignment.max_score} pts
        </span>
      </div>

      <h3 className="mt-3 font-display text-base font-semibold text-text-primary leading-snug">
        {assignment.title}
      </h3>

      <p className="mt-1.5 flex-1 text-sm text-text-secondary line-clamp-2">
        {assignment.description || 'No description available.'}
      </p>

      <div className="mt-4 flex items-center justify-between border-t border-navy-800 pt-4">
        <span className={cn(
          'flex items-center gap-1 text-xs',
          urgent ? 'font-medium text-status-warning' : 'text-text-secondary',
        )}>
          <Timer size={12} />
          {assignment.deadline ? formatRelative(assignment.deadline) : 'No deadline'}
        </span>
        <Link
          to={`/assignments/${assignment.id}`}
          className="inline-flex items-center gap-1 text-sm font-medium text-accent-blue hover:text-accent-teal transition-colors"
          aria-label={`View details for ${assignment.title}`}
        >
          View Details <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  )
}
