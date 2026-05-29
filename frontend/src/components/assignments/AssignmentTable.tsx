import type { AssignmentSummary } from '@/types/api'
import { DataTable } from '@/components/shared/DataTable'
import { Link } from 'react-router-dom'
import { Timer } from 'lucide-react'
import { formatRelative } from '@/lib/utils'

interface AssignmentTableProps {
  assignments: AssignmentSummary[]
}

export const AssignmentTable = ({ assignments }: AssignmentTableProps) => {
  const headers = ['Title', 'Category', 'Deadline', 'Max Score', '']
  const rows = assignments.map((assignment) => [
    assignment.title,
    assignment.category.replace('_', ' '),
    <span key={`deadline-${assignment.id}`} className="inline-flex items-center gap-1">
      <Timer size={14} />
      {assignment.deadline ? formatRelative(assignment.deadline) : 'No deadline'}
    </span>,
    assignment.max_score.toFixed(1),
    <Link
      key={`view-${assignment.id}`}
      to={`/assignments/${assignment.id}`}
      className="text-sm font-medium text-accent-blue"
    >
      View
    </Link>,
  ])

  return <DataTable headers={headers} rows={rows} />
}
