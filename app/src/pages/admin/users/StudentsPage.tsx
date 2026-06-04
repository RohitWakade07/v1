import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Users } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SkeletonRow } from '@/components/shared/SkeletonCard'
import { listStudents } from '@/api/admin/admin'
import { formatDate, shortId } from '@/lib/utils'

export const StudentsPage = () => {
  const [search, setSearch] = useState('')
  const { data: students = [], isLoading, error } = useQuery({
    queryKey: ['admin-students'],
    queryFn: listStudents,
    retry: false,
  })

  const filtered = students.filter(
    (s) =>
      s.full_name.toLowerCase().includes(search.toLowerCase()) ||
      s.roll_number.toLowerCase().includes(search.toLowerCase()) ||
      s.email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <PageWrapper>
      <PageHeader
        title="Students"
        description={`${students.length} total registered students`}
      />

      {/* Search */}
      <div className="mb-4 relative max-w-sm">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, roll no, or email…"
          className="input-dark pl-9"
        />
      </div>

      {/* Table */}
      <div className="card-dark overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-800">
                {['Student', 'Roll Number', 'Email', 'Status', 'Joined'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold tracking-widest text-text-secondary uppercase">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)
              ) : error ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-text-secondary text-sm">
                    <div className="flex flex-col items-center gap-2">
                      <Users size={32} className="text-navy-800" />
                      <p>Could not load students — admin API endpoint not yet available.</p>
                    </div>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-text-secondary text-sm">
                    No students found.
                  </td>
                </tr>
              ) : (
                filtered.map((student) => (
                  <tr
                    key={student.id}
                    className="border-b border-navy-800/50 hover:bg-navy-900/40 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-blue/15 text-accent-blue font-bold text-xs uppercase">
                          {student.full_name.charAt(0)}
                        </div>
                        <div>
                          <p className="font-medium text-text-primary">{student.full_name}</p>
                          <p className="text-xs text-text-secondary font-mono">{shortId(student.id)}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-text-secondary">{student.roll_number}</td>
                    <td className="px-4 py-3 text-text-secondary">{student.email}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={student.is_active ? 'active' : 'inactive'} />
                    </td>
                    <td className="px-4 py-3 text-text-secondary">{formatDate(student.created_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && !error && (
          <div className="border-t border-navy-800 px-4 py-2 text-xs text-text-secondary">
            Showing {filtered.length} of {students.length} students
          </div>
        )}
      </div>
    </PageWrapper>
  )
}

export default StudentsPage
