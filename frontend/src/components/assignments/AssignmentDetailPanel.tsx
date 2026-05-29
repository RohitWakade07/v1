import type { AssignmentDetail } from '@/types/api'

interface AssignmentDetailPanelProps {
  assignment: AssignmentDetail
}

export const AssignmentDetailPanel = ({ assignment }: AssignmentDetailPanelProps) => (
  <div className="rounded-xl border border-navy-800 bg-surface-light p-6 text-text-dark shadow-card">
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="text-xs font-semibold uppercase text-text-secondary">
          {assignment.category.replace('_', ' ')}
        </p>
        <h3 className="font-display text-2xl font-semibold text-text-dark">
          {assignment.title}
        </h3>
      </div>
      <div className="text-sm text-text-secondary">
        Max Score: {assignment.max_score}
      </div>
    </div>
    <p className="mt-4 text-sm text-text-dark">
      {assignment.description || 'No description provided.'}
    </p>
    <div className="mt-4 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-text-dark">
      {assignment.instructions ||
        'Evaluator instructions will be provided by your program administrators.'}
    </div>
  </div>
)
