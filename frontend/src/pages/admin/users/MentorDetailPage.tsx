import { useQuery } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { getMentorDetails, listMentorClassrooms } from '@/api/admin/admin'
import { formatDate } from '@/lib/utils'
import { SkeletonRow } from '@/components/shared/SkeletonCard'

import { useState } from 'react'
import { createPortal } from 'react-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateMentor, deleteMentor } from '@/api/admin/admin'
import { Pencil, Trash2, X } from 'lucide-react'
import type { UpdateMentorPayload } from '@/api/admin/admin'


export const MentorDetailPage = () => {
  const { mentorId } = useParams<{ mentorId: string }>()
  const navigate = useNavigate()

  const { data: mentor } = useQuery({
    queryKey: ['admin-mentor', mentorId],
    queryFn: () => getMentorDetails(mentorId!),
    enabled: !!mentorId
  })

  const { data: classrooms = [], isLoading: classroomsLoading } = useQuery({
    queryKey: ['admin-mentor-classrooms', mentorId],
    queryFn: () => listMentorClassrooms(mentorId!),
    enabled: !!mentorId
  })


  const queryClient = useQueryClient()
  const [showEditModal, setShowEditModal] = useState(false)
  const [form, setForm] = useState<UpdateMentorPayload>({})
  const [formError, setFormError] = useState('')

  const updateMutation = useMutation({
    mutationFn: (data: UpdateMentorPayload) => updateMentor(mentorId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-mentor', mentorId] })
      queryClient.invalidateQueries({ queryKey: ['admin-mentors'] })
      setShowEditModal(false)
      setFormError('')
    },
    onError: (err: any) => {
      setFormError(err?.response?.data?.detail ?? 'Failed to update mentor.')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteMentor(mentorId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-mentors'] })
      navigate('/admin/mentors')
    },
  })

  const handleEditClick = () => {
    if (mentor) {
      setForm({
        full_name: mentor.full_name,
        username: mentor.username,
        email: mentor.email,
        role: mentor.role as 'mentor' | 'admin',
        is_active: mentor.is_active,
      })
      setShowEditModal(true)
    }
  }

  const handleUpdate = () => {
    updateMutation.mutate(form)
  }

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this mentor? This action cannot be undone.')) {
      deleteMutation.mutate()
    }
  }

  const headers = ['Classroom Name', 'Join Code', 'Created At']

  const rows = classrooms.map(c => [
    <span key="name" className="font-medium text-text-primary">{c.name}</span>,
    <span key="code" className="font-mono text-text-secondary">{c.join_code}</span>,
    <span key="date" className="text-sm text-text-secondary">{formatDate(c.created_at)}</span>,
  ])

  return (
    <PageWrapper>
      <div className="mb-4 text-sm text-text-secondary">
        <button onClick={() => navigate('/admin/mentors')} className="hover:text-text-primary underline">Mentors</button>
        {' > '} {mentor?.full_name || 'Details'}
      </div>
      
      <div className="flex items-center justify-between">
        <PageHeader
          title={mentor?.full_name || 'Mentor Details'}
          description={mentor?.email}
        />
        <div className="flex gap-2">
          <button
            onClick={handleEditClick}
            className="flex items-center gap-2 rounded-lg bg-navy-800 px-4 py-2 text-sm font-semibold text-text-primary hover:bg-navy-700 transition-colors"
          >
            <Pencil size={15} /> Edit
          </button>
          <button
            onClick={handleDelete}
            className="flex items-center gap-2 rounded-lg bg-status-danger/10 px-4 py-2 text-sm font-semibold text-status-danger hover:bg-status-danger/20 transition-colors"
          >
            <Trash2 size={15} /> Delete
          </button>
        </div>
      </div>

      
      <div className="card-dark p-5 mt-6">
        <h3 className="text-lg font-semibold text-text-primary mb-4">Classrooms Created</h3>
        {classroomsLoading ? (
          <table className="w-full text-left text-sm text-text-secondary">
            <tbody>
              <SkeletonRow />
              <SkeletonRow />
            </tbody>
          </table>
        ) : (
          <DataTable 
            headers={headers} 
            rows={rows} 
            onRowClick={(index) => navigate(`/admin/classrooms/${classrooms[index].id}`)} 
          />
        )}
      </div>

      {/* Edit Mentor Modal */}
      {showEditModal && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-md rounded-2xl border border-navy-800 bg-navy-900 p-6 shadow-2xl">
            <button
              onClick={() => setShowEditModal(false)}
              className="absolute right-4 top-4 text-text-secondary hover:text-text-primary"
            >
              <X size={18} />
            </button>

            <h2 className="mb-1 font-display text-lg font-bold text-text-primary">Edit Mentor / Admin</h2>
            
            <div className="mt-4 space-y-3">
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary uppercase tracking-wider">Full Name</label>
                <input
                  className="input-dark w-full"
                  value={form.full_name || ''}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary uppercase tracking-wider">Username</label>
                <input
                  className="input-dark w-full font-mono"
                  value={form.username || ''}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary uppercase tracking-wider">Email</label>
                <input
                  type="email"
                  className="input-dark w-full"
                  value={form.email || ''}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary uppercase tracking-wider">New Password (Leave blank to keep current)</label>
                <input
                  type="password"
                  className="input-dark w-full"
                  placeholder="Set a new password"
                  value={form.password || ''}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                />
              </div>
              <div className="flex items-center gap-2 mt-4 mb-2">
                <input 
                  type="checkbox" 
                  id="isActiveCheck"
                  checked={form.is_active || false}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  className="rounded bg-navy-800 border-navy-700 text-accent-blue focus:ring-accent-blue/50"
                />
                <label htmlFor="isActiveCheck" className="text-sm font-medium text-text-primary">Account is Active</label>
              </div>
            </div>

            {formError && (
              <p className="mt-3 rounded-lg border border-status-danger/30 bg-status-danger/10 px-3 py-2 text-xs text-status-danger">
                {formError}
              </p>
            )}

            <div className="mt-5 flex gap-3">
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 rounded-lg border border-navy-700 px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdate}
                disabled={updateMutation.isPending}
                className="flex-1 rounded-lg bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:bg-accent-blue/80 transition-colors disabled:opacity-50"
              >
                {updateMutation.isPending ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

    </PageWrapper>
  )
}

export default MentorDetailPage
