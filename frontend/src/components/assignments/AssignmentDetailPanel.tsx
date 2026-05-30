import { Timer, Award, Download, BookOpen } from 'lucide-react'
import type { AssignmentDetail } from '@/types/api'
import { CategoryBadge } from '@/components/shared/StatusBadge'
import { formatDate, formatRelative } from '@/lib/utils'
import { cn } from '@/lib/utils'

const isUrgent = (deadline?: string) => {
  if (!deadline) return false
  return new Date(deadline).getTime() - Date.now() < 48 * 3600 * 1000
}

interface AssignmentDetailPanelProps {
  assignment: AssignmentDetail
}

export const AssignmentDetailPanel = ({ assignment }: AssignmentDetailPanelProps) => {
  const urgent = isUrgent(assignment.deadline)

  return (
    <div className="space-y-5">
      {/* Main detail card — light surface */}
      <div className="rounded-xl border border-slate-200 bg-surface-light p-6 shadow-card">
        {/* Header row */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <CategoryBadge category={assignment.category} />
            <h2 className="mt-2 font-display text-2xl font-bold text-text-dark">
              {assignment.title}
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className={cn(
              'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold',
              urgent
                ? 'bg-status-warning/15 text-status-warning border border-status-warning/30'
                : 'bg-slate-200 text-slate-600',
            )}>
              <Timer size={11} />
              {assignment.deadline ? (urgent ? `⚠ ${formatRelative(assignment.deadline)}` : formatRelative(assignment.deadline)) : 'No deadline'}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">
              <Award size={11} />
              {assignment.max_score} pts max
            </span>
          </div>
        </div>

        {/* Description */}
        <p className="mt-4 text-sm leading-relaxed text-text-dark">
          {assignment.description || 'No description provided for this assignment.'}
        </p>

        {/* Deadline absolute */}
        {assignment.deadline && (
          <p className="mt-3 text-xs text-slate-500">
            Deadline: {formatDate(assignment.deadline)}
          </p>
        )}
      </div>

      {/* Instructions */}
      <div className="rounded-xl border border-slate-200 bg-surface-light p-6 shadow-card">
        <div className="mb-3 flex items-center gap-2">
          <BookOpen size={16} className="text-accent-blue" />
          <h3 className="font-display text-base font-semibold text-text-dark">Instructions</h3>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-5 py-4 text-sm text-text-dark leading-relaxed">
          {assignment.instructions || (
            <span className="text-slate-400 italic">
              Evaluator instructions will be provided by your program administrators.
            </span>
          )}
        </div>
      </div>

      {/* Evaluator download placeholder */}
      <div className="flex items-center gap-4 rounded-xl border border-navy-800 bg-navy-900/50 p-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-blue/15 text-accent-blue">
          <Download size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold text-text-primary">Evaluator Binary</p>
          <p className="mt-0.5 text-xs text-text-secondary">
            Evaluator available — check your programme resources or contact your mentor to obtain the evaluator package.
          </p>
        </div>
      </div>
    </div>
  )
}
