import { useState } from 'react'
import { Modal } from '@/components/shared/Modal'
import { Assignment } from '@/types/api'
import { useUpdateAssignment } from '@/hooks/mentor/useUpdateAssignment'

interface Props {
  assignment: Assignment | null
  onClose: () => void
}

export function EditAssignmentModal({ assignment, onClose }: Props) {
  const [deadline, setDeadline] = useState(
    assignment?.deadline ? new Date(assignment.deadline).toISOString().slice(0, 16) : ''
  )
  const [maxScore, setMaxScore] = useState(assignment?.max_score?.toString() || '5')
  const updateMut = useUpdateAssignment()

  if (!assignment) return null

  const handleSave = async () => {
    await updateMut.mutateAsync({
      id: assignment.id,
      data: {
        deadline: deadline || undefined,
        max_score: parseInt(maxScore) || 5,
      },
    })
    onClose()
  }

  return (
    <Modal isOpen={!!assignment} onClose={onClose} title="Edit Assignment">
      <div className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">
            Deadline (Local Time)
          </label>
          <input
            type="datetime-local"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            className="input-dark w-full"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">
            Max Score
          </label>
          <input
            type="number"
            value={maxScore}
            onChange={(e) => setMaxScore(e.target.value)}
            className="input-dark w-full"
            min="1"
          />
        </div>
        <div className="flex justify-end gap-2 pt-4 border-t border-navy-800">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button
            onClick={handleSave}
            disabled={updateMut.isPending}
            className="btn-primary bg-accent-blue hover:bg-accent-blue/80"
          >
            {updateMut.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </Modal>
  )
}
