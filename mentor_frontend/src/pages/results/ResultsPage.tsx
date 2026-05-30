import { useMemo, useState } from 'react'
import { ClipboardCheck, Search } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { EmptyState } from '@/components/shared/EmptyState'
import { useMentorResults } from '@/hooks/useMentor'
import { formatDate } from '@/lib/utils'

export const ResultsPage = () => {
  const { data: results, isLoading } = useMentorResults()
  const [searchTerm, setSearchTerm] = useState('')

  const filteredData = useMemo(() => {
    if (!results) return []
    return results.filter((r) => {
      const matchesSearch = 
        r.student_roll.toLowerCase().includes(searchTerm.toLowerCase()) || 
        r.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.assignment_title.toLowerCase().includes(searchTerm.toLowerCase())
      
      return matchesSearch
    })
  }, [results, searchTerm])

  const headers = ['Student', 'Assignment', 'Score', 'Completed At']

  const rows = useMemo(() => {
    return filteredData.map((r) => [
      <div key="student">
        <p className="font-medium text-sm text-text-primary">{r.student_name}</p>
        <p className="font-mono text-xs text-text-secondary">{r.student_roll}</p>
      </div>,
      <span key="assignment" className="text-sm text-text-primary">{r.assignment_title}</span>,
      <span key="score" className="text-sm font-medium text-text-primary">
        <span className={r.final_score >= r.max_score * 0.5 ? 'text-accent-teal' : 'text-status-warning'}>
          {r.final_score.toFixed(1)}
        </span> 
        <span className="text-text-secondary text-xs ml-1">/ {r.max_score}</span>
      </span>,
      <span key="completed" className="text-xs text-text-secondary">{formatDate(r.completed_at)}</span>,
    ])
  }, [filteredData])

  return (
    <PageWrapper>
      <PageHeader
        title="Results & Submissions"
        description="Review student submissions, verified proofs, and final scores."
      />

      <div className="card-dark p-5">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 items-center gap-4">
            <div className="relative w-full max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" size={16} />
              <input
                type="text"
                placeholder="Search by student or assignment..."
                className="input-dark w-full pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-10 rounded-lg bg-navy-900" />
            <div className="h-10 rounded-lg bg-navy-900" />
            <div className="h-10 rounded-lg bg-navy-900" />
          </div>
        ) : filteredData.length === 0 ? (
          <EmptyState
            icon={<ClipboardCheck size={24} />}
            title="No results found"
            message={searchTerm ? "Try adjusting your search query." : "No completed results available."}
          />
        ) : (
          <DataTable headers={headers} rows={rows} />
        )}
      </div>
    </PageWrapper>
  )
}

export default ResultsPage
