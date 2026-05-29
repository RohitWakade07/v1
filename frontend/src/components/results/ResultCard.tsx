import type { ResultSummary } from '@/types/api'
import { Trophy } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { Link } from 'react-router-dom'

interface ResultCardProps {
  result: ResultSummary
}

export const ResultCard = ({ result }: ResultCardProps) => (
  <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-accent-teal">
        <Trophy size={18} />
        <span className="text-xs font-semibold uppercase">Completed</span>
      </div>
      <span className="text-xs text-text-secondary">
        {formatDate(result.completed_at)}
      </span>
    </div>
    <h3 className="mt-3 font-display text-lg font-semibold text-text-primary">
      {result.assignment_title}
    </h3>
    <p className="mt-1 text-sm text-text-secondary">
      {result.category.replace('_', ' ')}
    </p>
    <div className="mt-4 flex items-center justify-between text-sm">
      <span className="font-medium text-text-primary">
        {result.final_score.toFixed(1)} / {result.max_score.toFixed(1)}
      </span>
      <Link className="text-accent-blue" to={`/results/${result.id}`}>
        View Details
      </Link>
    </div>
  </div>
)
