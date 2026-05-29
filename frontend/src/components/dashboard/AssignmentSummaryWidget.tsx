import type { AssignmentSummary } from '@/types/api'
import { Timer } from 'lucide-react'
import { formatRelative } from '@/lib/utils'

interface AssignmentSummaryWidgetProps {
  assignments: AssignmentSummary[]
}

export const AssignmentSummaryWidget = ({
  assignments,
}: AssignmentSummaryWidgetProps) => (
  <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
    <h3 className="font-display text-lg font-semibold text-text-primary">
      Recent Assignments
    </h3>
    <div className="mt-4 space-y-3">
      {assignments.map((assignment) => (
        <div key={assignment.id} className="flex items-center justify-between">
          <div>
            <p className="text-sm text-text-primary">{assignment.title}</p>
            <p className="text-xs text-text-secondary">
              {assignment.category.replace('_', ' ')}
            </p>
          </div>
          <span className="inline-flex items-center gap-1 text-xs text-text-secondary">
            <Timer size={14} />
            {assignment.deadline ? formatRelative(assignment.deadline) : 'No deadline'}
          </span>
        </div>
      ))}
    </div>
  </div>
)
