import { useState, useEffect } from 'react'
import { Modal } from '@/components/shared/Modal'
import { Assignment } from '@/types/api'
import { useAdminUpdateAssignment } from '@/hooks/admin/useAdminUpdateAssignment'
import { Settings, FileText } from 'lucide-react'

interface Props {
  assignment: Assignment | null
  onClose: () => void
}

type Tab = 'general' | 'submission'

export function EditAssignmentModal({ assignment, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('general')

  // General Info fields
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [deadline, setDeadline] = useState('')
  const [maxScore, setMaxScore] = useState('5')
  const [latePenaltyPct, setLatePenaltyPct] = useState('0')
  const [category, setCategory] = useState('')

  // Submission Info fields
  const [submissionFilename, setSubmissionFilename] = useState('')
  const [submissionInstructions, setSubmissionInstructions] = useState('')

  const updateMut = useAdminUpdateAssignment()

  useEffect(() => {
    if (assignment) {
      setTitle(assignment.title || '')
      setDescription(assignment.description || '')
      setDeadline(assignment.deadline ? new Date(assignment.deadline).toISOString().slice(0, 16) : '')
      setMaxScore(assignment.max_score?.toString() || '5')
      setLatePenaltyPct(assignment.late_penalty_pct?.toString() || '0')
      setCategory(assignment.category || '')
      setSubmissionFilename(assignment.submission_filename || '')
      setSubmissionInstructions(assignment.submission_instructions || '')
      setActiveTab('general')
    }
  }, [assignment])

  if (!assignment) return null

  const handleSave = async () => {
    await updateMut.mutateAsync({
      id: assignment.id,
      data: {
        title: title || undefined,
        description: description || undefined,
        deadline: deadline || undefined,
        max_score: parseFloat(maxScore) || 5,
        late_penalty_pct: parseFloat(latePenaltyPct) || 0,
        submission_filename: submissionFilename || undefined,
        submission_instructions: submissionInstructions || undefined,
      },
    })
    onClose()
  }

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'general', label: 'General Info', icon: <Settings size={13} /> },
    { id: 'submission', label: 'Submission Info', icon: <FileText size={13} /> },
  ]

  return (
    <Modal isOpen={!!assignment} onClose={onClose} title={`Edit: ${assignment.title}`}>
      {/* Tab Bar */}
      <div className="flex border-b border-navy-800 mb-5 -mt-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-accent-blue text-accent-blue'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      <div className="space-y-4 min-h-[280px]">
        {activeTab === 'general' && (
          <>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="input-dark w-full"
                placeholder="Assignment title"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="input-dark w-full resize-none"
                rows={3}
                placeholder="Brief description of the assignment"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Max Score</label>
                <input
                  type="number"
                  value={maxScore}
                  onChange={(e) => setMaxScore(e.target.value)}
                  className="input-dark w-full"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Late Penalty (%)</label>
                <input
                  type="number"
                  value={latePenaltyPct}
                  onChange={(e) => setLatePenaltyPct(e.target.value)}
                  className="input-dark w-full"
                  min="0"
                  max="100"
                  step="1"
                  placeholder="0"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Deadline (Local Time)</label>
              <input
                type="datetime-local"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="input-dark w-full"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Category</label>
              <input
                type="text"
                value={category}
                disabled
                className="input-dark w-full opacity-50 cursor-not-allowed"
                title="Category cannot be changed after creation"
              />
              <p className="text-[10px] text-text-muted mt-1">Category is locked after creation.</p>
            </div>
          </>
        )}

        {activeTab === 'submission' && (
          <>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                Required Submission Filename
              </label>
              <input
                type="text"
                value={submissionFilename}
                onChange={(e) => setSubmissionFilename(e.target.value)}
                className="input-dark w-full font-mono"
                placeholder="e.g. analyze.sh or RECOVERY.md"
              />
              <p className="text-[10px] text-text-muted mt-1">
                The exact filename students must include in their ZIP. Leave blank to hide the file tree.
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                Submission Instructions
              </label>
              <textarea
                value={submissionInstructions}
                onChange={(e) => setSubmissionInstructions(e.target.value)}
                className="input-dark w-full resize-none"
                rows={8}
                placeholder="Detailed submission instructions shown to students on the assignment page. Supports plain text."
              />
              <p className="text-[10px] text-text-muted mt-1">
                These instructions replace the hardcoded steps on the assignment detail page.
              </p>
            </div>
          </>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t border-navy-800 mt-4">
        <button onClick={onClose} className="btn-secondary">Cancel</button>
        <button
          onClick={handleSave}
          disabled={updateMut.isPending}
          className="btn-primary bg-accent-blue hover:bg-accent-blue/80"
        >
          {updateMut.isPending ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </Modal>
  )
}
