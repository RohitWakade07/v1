import type { AssignmentSummary } from '@/types/api'
import { Link } from 'react-router-dom'
import { Timer } from 'lucide-react'
import { CategoryBadge } from '@/components/shared/StatusBadge'
import { formatRelative } from '@/lib/utils'
import { cn } from '@/lib/utils'

const isUrgent = (deadline?: string) => {
  if (!deadline) return false
  return new Date(deadline).getTime() - Date.now() < 48 * 3600 * 1000
}

interface AssignmentTableProps {
  assignments: AssignmentSummary[]
}

export const AssignmentTable = ({ assignments }: AssignmentTableProps) => {
  return (
    <div className="overflow-hidden rounded-xl border border-navy-800">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="bg-navy-900/80 sticky top-0">
            <tr>
              {['Title', 'Category', 'Deadline', 'Max Score', ''].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {assignments.map((a, i) => {
              const urgent = isUrgent(a.deadline)
              return (
                <tr
                  key={a.id}
                  className={cn(
                    'border-t border-navy-800 transition-colors hover:bg-navy-800/60',
                    i % 2 === 0 ? 'bg-navy-950' : 'bg-navy-900/30',
                  )}
                >
                  <td className="px-4 py-3 font-medium text-text-primary max-w-xs">
                    <p className="truncate">{a.title}</p>
                  </td>
                  <td className="px-4 py-3">
                    <CategoryBadge category={a.category} />
                  </td>
                  <td className={cn('px-4 py-3', urgent ? 'text-status-warning font-medium' : 'text-text-secondary')}>
                    <span className="inline-flex items-center gap-1">
                      <Timer size={12} />
                      {a.deadline ? formatRelative(a.deadline) : 'No deadline'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-text-primary">{a.max_score.toFixed(1)}</td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/student/assignments/${a.id}`}
                      className="inline-flex items-center gap-1 rounded-lg bg-accent-blue/10 px-3 py-1 text-xs font-medium text-accent-blue transition-colors hover:bg-accent-blue hover:text-white"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
