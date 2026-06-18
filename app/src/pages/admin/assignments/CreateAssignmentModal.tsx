import { useState } from 'react'
import { Modal } from '@/components/shared/Modal'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { useNotificationStore } from '@/store/notificationStore'
import type { Assignment } from '@/types/api'

interface Props {
  isOpen: boolean
  onClose: () => void
}

const CATEGORIES = [
  { value: 'artifact_validation', label: 'Artifact Validation' },
  { value: 'deterministic_execution', label: 'Deterministic Execution' },
  { value: 'filesystem_validation', label: 'Filesystem Validation' },
  { value: 'git_validation', label: 'Git Validation' },
  { value: 'network_validation', label: 'Network Validation' },
  { value: 'documentation_review', label: 'Documentation Review' },
  { value: 'manual_review', label: 'Manual Review' },
]

export function CreateAssignmentModal({ isOpen, onClose }: Props) {
  const [slug, setSlug] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('filesystem_validation')
  const [maxScore, setMaxScore] = useState('5')
  const [deadline, setDeadline] = useState('')
  const [latePenaltyPct, setLatePenaltyPct] = useState('0')
  const [submissionFilename, setSubmissionFilename] = useState('')
  const [submissionInstructions, setSubmissionInstructions] = useState('')

  const qc = useQueryClient()
  const addNotification = useNotificationStore((s) => s.addNotification)

  const createMut = useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const { data: result } = await apiClient.post<Assignment>('/assignments', data)
      return result
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-assignments'] })
      addNotification({ type: 'success', title: 'Assignment created', message: 'New assignment created successfully.' })
      handleClose()
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to create assignment.'
      addNotification({ type: 'error', title: 'Create failed', message: String(msg) })
    },
  })

  const handleClose = () => {
    setSlug(''); setTitle(''); setDescription(''); setCategory('filesystem_validation')
    setMaxScore('5'); setDeadline(''); setLatePenaltyPct('0')
    setSubmissionFilename(''); setSubmissionInstructions('')
    onClose()
  }

  const handleCreate = () => {
    if (!slug || !title || !category) {
      addNotification({ type: 'error', title: 'Validation error', message: 'Slug, title and category are required.' })
      return
    }
    createMut.mutate({
      slug: slug.toLowerCase().trim(),
      title,
      description: description || undefined,
      category,
      max_score: parseFloat(maxScore) || 5,
      deadline: deadline || undefined,
      late_penalty_pct: parseFloat(latePenaltyPct) || 0,
      submission_filename: submissionFilename || undefined,
      submission_instructions: submissionInstructions || undefined,
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Assignment">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">Slug <span className="text-status-danger">*</span></label>
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="input-dark w-full font-mono"
              placeholder="week5"
            />
            <p className="text-[10px] text-text-muted mt-1">Unique identifier, e.g. week5</p>
          </div>
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">Category <span className="text-status-danger">*</span></label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="input-dark w-full"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Title <span className="text-status-danger">*</span></label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input-dark w-full"
            placeholder="Week 5: ..."
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input-dark w-full resize-none"
            rows={2}
            placeholder="Brief description..."
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">Max Score</label>
            <input type="number" value={maxScore} onChange={(e) => setMaxScore(e.target.value)} className="input-dark w-full" min="1" />
          </div>
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">Late Penalty (%)</label>
            <input type="number" value={latePenaltyPct} onChange={(e) => setLatePenaltyPct(e.target.value)} className="input-dark w-full" min="0" max="100" />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Deadline (Local Time)</label>
          <input type="datetime-local" value={deadline} onChange={(e) => setDeadline(e.target.value)} className="input-dark w-full" />
        </div>

        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Required Filename</label>
          <input
            type="text"
            value={submissionFilename}
            onChange={(e) => setSubmissionFilename(e.target.value)}
            className="input-dark w-full font-mono"
            placeholder="e.g. script.sh"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Submission Instructions</label>
          <textarea
            value={submissionInstructions}
            onChange={(e) => setSubmissionInstructions(e.target.value)}
            className="input-dark w-full resize-none"
            rows={3}
            placeholder="Instructions shown to students..."
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t border-navy-800 mt-4">
        <button onClick={handleClose} className="btn-secondary">Cancel</button>
        <button
          onClick={handleCreate}
          disabled={createMut.isPending}
          className="btn-primary bg-accent-teal hover:bg-accent-teal/80"
        >
          {createMut.isPending ? 'Creating...' : 'Create Assignment'}
        </button>
      </div>
    </Modal>
  )
}
