import { useMemo, useState } from 'react'
import { Users, Search } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { EmptyState } from '@/components/shared/EmptyState'
import { useMentorStudents } from '@/hooks/useMentor'

export const StudentsPage = () => {
  const { data: students, isLoading } = useMentorStudents()
  const [searchTerm, setSearchTerm] = useState('')

  const filteredData = useMemo(() => {
    if (!students) return []
    return students.filter((s) => 
      s.full_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
      s.roll_number.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [students, searchTerm])

  const headers = ['Roll Number', 'Full Name', 'Email', 'Assignments Participated', 'Total Sessions']

  const rows = useMemo(() => {
    return filteredData.map((s) => [
      <span key="roll" className="font-mono text-sm text-text-primary">{s.roll_number}</span>,
      <span key="name" className="font-medium text-text-primary">{s.full_name}</span>,
      <span key="email" className="text-sm text-text-secondary">{s.email}</span>,
      <span key="assignments" className="text-sm font-medium text-text-primary">{s.assignments_participated}</span>,
      <span key="sessions" className="text-sm font-medium text-text-primary">{s.sessions_count}</span>,
    ])
  }, [filteredData])

  return (
    <PageWrapper>
      <PageHeader
        title="Students"
        description="View students who have participated in your assignments."
      />

      <div className="card-dark p-5">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 items-center gap-4">
            <div className="relative w-full max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" size={16} />
              <input
                type="text"
                placeholder="Search by name or roll number..."
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
            icon={<Users size={24} />}
            title="No students found"
            message={searchTerm ? "Try adjusting your search query." : "No students have participated in your assignments yet."}
          />
        ) : (
          <DataTable headers={headers} rows={rows} />
        )}
      </div>
    </PageWrapper>
  )
}

export default StudentsPage
