import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, UserCheck } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SkeletonRow } from '@/components/shared/SkeletonCard'
import { listMentors } from '@/api/admin/admin'
import { formatDate, shortId } from '@/lib/utils'

export const MentorsPage = () => {
  const [search, setSearch] = useState('')
  const { data: mentors = [], isLoading, error } = useQuery({
    queryKey: ['admin-mentors'],
    queryFn: listMentors,
    retry: false,
  })

  const filtered = mentors.filter(
    (m) =>
      m.full_name.toLowerCase().includes(search.toLowerCase()) ||
      m.username.toLowerCase().includes(search.toLowerCase()) ||
      m.email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <PageWrapper>
      <PageHeader
        title="Mentors"
        description={`${mentors.length} total instructors`}
      />

      <div className="mb-4 relative max-w-sm">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, username, or email…"
          className="input-dark pl-9"
        />
      </div>

      <div className="card-dark overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-800">
                {['Mentor', 'Username', 'Email', 'Role', 'Status', 'Joined'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold tracking-widest text-text-secondary uppercase">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => <SkeletonRow key={i} />)
              ) : error ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-text-secondary text-sm">
                    <div className="flex flex-col items-center gap-2">
                      <UserCheck size={32} className="text-navy-800" />
                      <p>Could not load mentors — admin API endpoint not yet available.</p>
                    </div>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-text-secondary text-sm">
                    No mentors found.
                  </td>
                </tr>
              ) : (
                filtered.map((mentor) => (
                  <tr key={mentor.id} className="border-b border-navy-800/50 hover:bg-navy-900/40 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-teal/15 text-accent-teal font-bold text-xs uppercase">
                          {mentor.full_name.charAt(0)}
                        </div>
                        <div>
                          <p className="font-medium text-text-primary">{mentor.full_name}</p>
                          <p className="text-xs text-text-secondary font-mono">{shortId(mentor.id)}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-text-secondary">{mentor.username}</td>
                    <td className="px-4 py-3 text-text-secondary">{mentor.email}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-accent-blue/10 text-accent-blue border border-accent-blue/20 uppercase">
                        {mentor.role}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={mentor.is_active ? 'active' : 'inactive'} />
                    </td>
                    <td className="px-4 py-3 text-text-secondary">{formatDate(mentor.created_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && !error && (
          <div className="border-t border-navy-800 px-4 py-2 text-xs text-text-secondary">
            Showing {filtered.length} of {mentors.length} mentors
          </div>
        )}
      </div>
    </PageWrapper>
  )
}

export default MentorsPage
