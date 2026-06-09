import { Trophy, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { ResultSummary } from '@/types/api'
import { CategoryBadge } from '@/components/shared/StatusBadge'
import { formatDate } from '@/lib/utils'

interface ResultCardProps {
  result: ResultSummary
}

export const ResultCard = ({ result }: ResultCardProps) => {
  const pct = Math.min(100, Math.round((result.final_score / result.max_score) * 100))
  const scoreColor =
    pct >= 80 ? 'bg-accent-teal' : pct >= 50 ? 'bg-accent-blue' : 'bg-status-danger'

  return (
    <div className="card-dark transition-card flex flex-col p-5">
      <div className="flex items-start justify-between gap-2">
        <CategoryBadge category={result.category} />
        <span className="text-xs text-text-secondary">{formatDate(result.completed_at)}</span>
      </div>

      <h3 className="mt-3 font-display text-base font-semibold text-text-primary leading-snug">
        {result.assignment_title}
      </h3>

      {/* Score */}
      <div className="mt-4 flex items-end justify-between gap-3">
        <div className="flex items-center gap-2">
          <Trophy size={16} className="text-accent-teal shrink-0" />
          <span className="font-display text-xl font-bold text-accent-teal">
            {result.final_score.toFixed(1)}
          </span>
          <span className="text-sm text-text-secondary">/ {result.max_score}</span>
        </div>
        <span className="text-sm font-semibold text-text-secondary">{pct}%</span>
      </div>

      {/* Progress bar */}
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-navy-800">
        <div
          className={`h-full rounded-full transition-all ${scoreColor}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Score: ${pct}%`}
        />
      </div>

      <div className="mt-4 flex justify-end border-t border-navy-800 pt-4">
        <Link
          to={`/student/results/${result.id}`}
          className="inline-flex items-center gap-1 text-sm font-medium text-accent-blue hover:text-accent-teal transition-colors"
          aria-label={`View full result for ${result.assignment_title}`}
        >
          View Breakdown <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  )
}
