import { Timer } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { AssignmentSummary } from '@/types/api'
import { CategoryBadge } from '@/components/shared/StatusBadge'
import { formatRelative } from '@/lib/utils'

const isUrgent = (deadline?: string) => {
  if (!deadline) return false
  return new Date(deadline).getTime() - Date.now() < 48 * 3600 * 1000
}

interface AssignmentSummaryWidgetProps {
  assignments: AssignmentSummary[]
}

export const AssignmentSummaryWidget = ({ assignments }: AssignmentSummaryWidgetProps) => (
  <div className="card-dark p-5">
    <div className="mb-4 flex items-center justify-between">
      <h3 className="font-display text-base font-semibold text-text-primary">Recent Assignments</h3>
      <Link to="/student/assignments" className="text-xs text-accent-blue hover:text-accent-teal transition-colors">
        View all →
      </Link>
    </div>
    {assignments.length === 0 ? (
      <p className="text-center text-sm text-text-secondary py-6">No assignments published yet.</p>
    ) : (
      <div className="space-y-3">
        {assignments.map((a) => {
          const urgent = isUrgent(a.deadline)
          return (
            <Link
              key={a.id}
              to={`/student/assignments/${a.id}`}
              className="flex items-center justify-between gap-3 rounded-lg p-2 transition-colors hover:bg-navy-800/40"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-text-primary">{a.title}</p>
                <CategoryBadge category={a.category} className="mt-1" />
              </div>
              <div className={`flex shrink-0 items-center gap-1 text-xs ${urgent ? 'text-status-warning font-medium' : 'text-text-secondary'}`}>
                <Timer size={12} />
                {a.deadline ? formatRelative(a.deadline) : 'No deadline'}
              </div>
            </Link>
          )
        })}
      </div>
    )}
  </div>
)
