import { FileCheck2 } from 'lucide-react'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatDate } from '@/lib/utils'
import type { SessionSummary } from '@/types/api'

interface ProofHistoryTableProps {
  sessions: SessionSummary[]
}

export const ProofHistoryTable = ({ sessions }: ProofHistoryTableProps) => {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-center">
        <FileCheck2 size={24} className="text-text-secondary" />
        <p className="text-sm text-text-secondary">No proof submissions for this session yet.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-navy-800">
      <table className="w-full border-collapse text-sm">
        <thead className="bg-navy-900/80">
          <tr>
            {['Session', 'Status', 'Submitted', 'Score'].map((h) => (
              <th key={h} className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sessions.map((s, i) => (
            <tr key={s.id} className={`border-t border-navy-800 ${i % 2 === 0 ? 'bg-navy-950' : 'bg-navy-900/30'}`}>
              <td className="px-4 py-2 font-mono text-xs text-text-primary">{s.id.slice(0, 12)}…</td>
              <td className="px-4 py-2"><StatusBadge status={s.status} /></td>
              <td className="px-4 py-2 text-xs text-text-secondary">{formatDate(s.submitted_at)}</td>
              <td className="px-4 py-2 text-xs font-medium text-accent-teal">
                {s.final_score !== null && s.final_score !== undefined ? s.final_score.toFixed(1) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
