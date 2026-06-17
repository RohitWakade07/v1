import { useState } from 'react'
import { createPortal } from 'react-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, UserCheck, UserPlus, X } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SkeletonRow } from '@/components/shared/SkeletonCard'
import { listMentors, createMentor } from '@/api/admin/admin'
import type { CreateMentorPayload } from '@/api/admin/admin'
import { formatDate, shortId } from '@/lib/utils'

const EMPTY_FORM: CreateMentorPayload = {
  username: '',
  full_name: '',
  email: '',
  password: '',
  role: 'mentor',
}

export const MentorsPage = () => {
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState<CreateMentorPayload>(EMPTY_FORM)
  const [formError, setFormError] = useState('')

  const queryClient = useQueryClient()

  const { data: mentors = [], isLoading, error } = useQuery({
    queryKey: ['admin-mentors'],
    queryFn: listMentors,
    retry: false,
  })

  const mutation = useMutation({
    mutationFn: createMentor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-mentors'] })
      setShowModal(false)
      setForm(EMPTY_FORM)
      setFormError('')
    },
    onError: (err: any) => {
      setFormError(err?.response?.data?.detail ?? 'Failed to create mentor.')
    },
  })

  const filtered = mentors.filter(
    (m) =>
      m.full_name.toLowerCase().includes(search.toLowerCase()) ||
      m.username.toLowerCase().includes(search.toLowerCase()) ||
      m.email.toLowerCase().includes(search.toLowerCase())
  )

  const handleSubmit = () => {
    if (!form.username || !form.full_name || !form.email || !form.password) {
      setFormError('All fields are required.')
      return
    }
    setFormError('')
    mutation.mutate(form)
  }

  return (
    <PageWrapper>
      <div className="flex items-center justify-between mb-1">
        <PageHeader
          title="Mentors"
          description={`${mentors.length} total instructors`}
        />
        <button
          onClick={() => { setShowModal(true); setFormError('') }}
          className="flex items-center gap-2 rounded-lg bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:bg-accent-blue/80 transition-colors"
        >
          <UserPlus size={15} />
          Add Mentor
        </button>
      </div>

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
                      <p>Could not load mentors.</p>
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

      {/* Create Mentor Modal */}
      {showModal && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-md rounded-2xl border border-navy-800 bg-navy-900 p-6 shadow-2xl">
            <button
              onClick={() => { setShowModal(false); setForm(EMPTY_FORM); setFormError('') }}
              className="absolute right-4 top-4 text-text-secondary hover:text-text-primary"
            >
              <X size={18} />
            </button>

            <h2 className="mb-1 font-display text-lg font-bold text-text-primary">Add Mentor / Admin</h2>
            <p className="mb-5 text-xs text-text-secondary">Create a new staff account on the platform.</p>

            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary uppercase tracking-wider">Full Name</label>
                <input
                  className="input-dark w-full"
                  placeholder="e.g. Rahul Sharma"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary uppercase tracking-wider">Username</label>
                <input
                  className="input-dark w-full font-mono"
                  placeholder="e.g. rahul.sharma"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary uppercase tracking-wider">Email</label>
                <input
                  type="email"
                  className="input-dark w-full"
                  placeholder="e.g. rahul@example.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary uppercase tracking-wider">Password</label>
                <input
                  type="password"
                  className="input-dark w-full"
                  placeholder="Set a strong password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary uppercase tracking-wider">Role</label>
                <select
                  className="input-dark w-full"
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value as 'mentor' | 'admin' })}
                >
                  <option value="mentor">Mentor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>

            {formError && (
              <p className="mt-3 rounded-lg border border-status-danger/30 bg-status-danger/10 px-3 py-2 text-xs text-status-danger">
                {formError}
              </p>
            )}

            <div className="mt-5 flex gap-3">
              <button
                onClick={() => { setShowModal(false); setForm(EMPTY_FORM); setFormError('') }}
                className="flex-1 rounded-lg border border-navy-700 px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={mutation.isPending}
                className="flex-1 rounded-lg bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:bg-accent-blue/80 transition-colors disabled:opacity-50"
              >
                {mutation.isPending ? 'Creating…' : 'Create Account'}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </PageWrapper>
  )
}

export default MentorsPage
