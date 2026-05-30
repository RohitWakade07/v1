import { CheckCircle2, Circle, Loader2 } from 'lucide-react'
import type { SessionDetail } from '@/types/api'
import { formatDate } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface TimelineStep {
  label: string
  timestamp?: string
  status: 'completed' | 'active' | 'pending'
  color: string
}

interface SessionTimelineProps {
  session: SessionDetail
}

export const SessionTimeline = ({ session }: SessionTimelineProps) => {
  const steps: TimelineStep[] = [
    {
      label: 'Session Created',
      timestamp: session.started_at,
      status: 'completed',
      color: 'text-accent-blue',
    },
    {
      label: 'Evaluation In Progress',
      timestamp: undefined,
      status:
        session.status === 'IN_PROGRESS' || session.status === 'COMPLETED' || session.status === 'REJECTED'
          ? 'completed'
          : session.status === 'STARTED'
          ? 'active'
          : 'pending',
      color: 'text-status-warning',
    },
    {
      label: 'Proof Submitted',
      timestamp: session.submitted_at,
      status:
        session.status === 'COMPLETED' || session.status === 'REJECTED'
          ? 'completed'
          : 'pending',
      color: 'text-accent-blue',
    },
    {
      label:
        session.status === 'REJECTED' ? 'Verification Failed' : 'Verification Complete',
      timestamp: session.completed_at,
      status:
        session.status === 'COMPLETED'
          ? 'completed'
          : session.status === 'REJECTED'
          ? 'active'
          : 'pending',
      color:
        session.status === 'REJECTED' ? 'text-status-danger' : 'text-accent-teal',
    },
  ]

  return (
    <div className="card-dark p-5">
      <h3 className="mb-5 font-display text-base font-semibold text-text-primary">
        Session Timeline
      </h3>
      <ol className="relative space-y-5 pl-6">
        <div className="absolute left-2.5 top-0 h-full w-px bg-navy-800" />
        {steps.map((step, i) => (
          <li key={i} className="relative flex flex-col">
            {/* dot */}
            <div className={cn('absolute -left-[18px] flex h-4 w-4 items-center justify-center rounded-full border-2 border-navy-800 bg-navy-950', step.color)}>
              {step.status === 'completed' ? (
                <CheckCircle2 size={12} />
              ) : step.status === 'active' ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Circle size={12} className="text-navy-800" />
              )}
            </div>
            <p className={cn(
              'text-sm font-medium',
              step.status === 'pending' ? 'text-text-secondary' : 'text-text-primary',
            )}>
              {step.label}
            </p>
            {step.timestamp && (
              <p className="mt-0.5 text-xs text-text-secondary">
                {formatDate(step.timestamp)}
              </p>
            )}
          </li>
        ))}
      </ol>
    </div>
  )
}
