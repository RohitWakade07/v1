import { FlaskConical } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { SubmissionPublic } from '@/types/api'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatRelative } from '@/lib/utils'

interface RecentActivityFeedProps {
  submissions: SubmissionPublic[]
}

export const RecentActivityFeed = ({ submissions }: RecentActivityFeedProps) => (
  <div className="card-dark p-5">
    <div className="mb-4 flex items-center justify-between">
      <h3 className="font-display text-base font-semibold text-text-primary">Recent Submissions</h3>
      <Link to="/student/assignments" className="text-xs text-accent-blue hover:text-accent-teal transition-colors">
        View all →
      </Link>
    </div>
    {submissions.length === 0 ? (
      <p className="text-center text-sm text-text-secondary py-6">No recent submissions. Start an assignment to begin.</p>
    ) : (
      <div className="space-y-3">
        {submissions.map((submission) => (
          <Link
            key={submission.id}
            to={`/student/submissions/${submission.id}`}
            className="flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-navy-800/40"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-blue/10 text-accent-blue">
              <FlaskConical size={15} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-text-primary">
                Attempt {submission.attempt_number}
              </p>
              <p className="text-xs text-text-secondary">
                {submission.submitted_at ? formatRelative(submission.submitted_at) : 'Just now'}
              </p>
            </div>
            <StatusBadge status={submission.status} />
          </Link>
        ))}
      </div>
    )}
  </div>
)
