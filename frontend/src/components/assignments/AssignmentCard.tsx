import { ArrowRight, Timer } from 'lucide-react'
import type { AssignmentSummary } from '@/types/api'
import { formatRelative } from '@/lib/utils'
import { Link } from 'react-router-dom'

interface AssignmentCardProps {
  assignment: AssignmentSummary
}

export const AssignmentCard = ({ assignment }: AssignmentCardProps) => (
  <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
    <div className="flex items-center justify-between">
      <span className="rounded-full bg-navy-800 px-3 py-1 text-xs text-text-secondary">
        {assignment.category.replace('_', ' ')}
      </span>
      <div className="flex items-center gap-1 text-xs text-text-secondary">
        <Timer size={14} />
        {assignment.deadline ? formatRelative(assignment.deadline) : 'No deadline'}
      </div>
    </div>
    <h3 className="mt-3 font-display text-lg font-semibold text-text-primary">
      {assignment.title}
    </h3>
    <p className="mt-2 text-sm text-text-secondary">
      {assignment.description || 'No description available yet.'}
    </p>
    <div className="mt-4 flex items-center justify-between">
      <span className="text-xs text-text-secondary">
        Max Score: {assignment.max_score}
      </span>
      <Link
        to={`/assignments/${assignment.id}`}
        className="inline-flex items-center gap-1 text-sm font-medium text-accent-blue"
      >
        View Details <ArrowRight size={14} />
      </Link>
    </div>
  </div>
)
