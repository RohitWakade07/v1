import { CheckCircle2, XCircle } from 'lucide-react'

interface ScoreBreakdownTableProps {
  breakdown: Record<string, { passed: boolean; score: number }>
}

export const ScoreBreakdownTable = ({ breakdown }: ScoreBreakdownTableProps) => {
  const rows = Object.entries(breakdown)

  return (
    <div className="overflow-hidden rounded-xl border border-navy-800">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-navy-900 text-text-secondary">
          <tr>
            <th className="px-4 py-3">Test</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Score</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([testId, result]) => (
            <tr key={testId} className="border-t border-navy-800">
              <td className="px-4 py-3 font-mono text-xs text-text-primary">
                {testId}
              </td>
              <td className="px-4 py-3">
                {result.passed ? (
                  <span className="inline-flex items-center gap-1 text-accent-teal">
                    <CheckCircle2 size={14} /> Passed
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-status-danger">
                    <XCircle size={14} /> Failed
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-text-primary">
                {result.score.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
