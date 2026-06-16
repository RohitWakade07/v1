import { useState, useMemo } from 'react'
import { FolderIcon, FileTextIcon, UsersIcon, ChevronRight } from 'lucide-react'
import { useClassrooms, useClassroomEnrollments, useMentorSubmissions } from '@/hooks/mentor/useMentor'
import { useAssignments } from '@/hooks/mentor/useAssignments'
import { DataTable } from '@/components/shared/DataTable'
import { EmptyState } from '@/components/shared/EmptyState'
import { Modal } from '@/components/shared/Modal'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatDateTime } from '@/lib/utils'


export const ClassroomHierarchyView = () => {
  const { data: classrooms, isLoading: loadingClassrooms } = useClassrooms()
  const { data: assignments, isLoading: loadingAssignments } = useAssignments()
  const { data: allSubmissions, isLoading: loadingSubmissions } = useMentorSubmissions()

  const [selectedClassroomId, setSelectedClassroomId] = useState<string | null>(null)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string | null>(null)
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null)

  const { data: enrollments, isLoading: loadingEnrollments } = useClassroomEnrollments(selectedClassroomId)



  // 2. Assignment Selection
  const selectedAssignment = useMemo(() => 
    assignments?.find(a => a.id === selectedAssignmentId), 
  [assignments, selectedAssignmentId])

  // 3. Derived Student Roster with Submission Status
  const studentRoster = useMemo(() => {
    if (!enrollments || !selectedAssignment || !allSubmissions) return []

    // Map all students in the classroom to their latest submission for this assignment
    return enrollments
      .filter(e => e.status === 'APPROVED')
      .map(enrollment => {
        // Find all submissions for this student + assignment
        const studentSubmissions = allSubmissions.filter(
          s => s.student_id === enrollment.student_id && s.assignment_id === selectedAssignment.id
        )

        // Sort by attempt number desc to get latest
        const latestSubmission = studentSubmissions.sort((a, b) => b.attempt_number - a.attempt_number)[0]

        return {
          student: enrollment,
          latestSubmission,
          submissionCount: studentSubmissions.length
        }
      })
  }, [enrollments, selectedAssignment, allSubmissions])

  // Data for the Student Detail Modal
  const selectedStudentSubmissions = useMemo(() => {
    if (!selectedStudentId || !selectedAssignment || !allSubmissions) return []
    return allSubmissions
      .filter(s => s.student_id === selectedStudentId && s.assignment_id === selectedAssignment.id)
      .sort((a, b) => b.attempt_number - a.attempt_number)
  }, [allSubmissions, selectedStudentId, selectedAssignment])

  const selectedStudentName = useMemo(() => {
    if (!selectedStudentId || !enrollments) return ''
    const enroll = enrollments.find(e => e.student_id === selectedStudentId)
    return enroll ? enroll.student_name : ''
  }, [selectedStudentId, enrollments])


  if (loadingClassrooms || loadingAssignments) {
    return (
      <div className="animate-pulse space-y-4 mt-6">
        <div className="h-10 rounded-lg bg-navy-900" />
        <div className="h-32 rounded-lg bg-navy-900" />
      </div>
    )
  }

  if (!classrooms || classrooms.length === 0) {
    return (
      <div className="mt-6">
        <EmptyState icon={<FolderIcon size={24} />} title="No Classrooms" message="You haven't created any classrooms yet." />
      </div>
    )
  }

  return (
    <div className="mt-6 space-y-6">
      {/* Step 1: Select Classroom */}
      <div className="card-dark p-5">
        <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4 flex items-center gap-2">
          <FolderIcon size={16} /> Select Classroom
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {classrooms.map(c => (
            <button
              key={c.id}
              onClick={() => {
                setSelectedClassroomId(c.id)
                setSelectedAssignmentId(null) // reset child selection
              }}
              className={`p-4 rounded-xl border text-left transition-all ${
                selectedClassroomId === c.id 
                  ? 'bg-navy-800 border-accent-teal shadow-lg shadow-accent-teal/10' 
                  : 'bg-navy-900 border-navy-700 hover:border-navy-600'
              }`}
            >
              <div className="font-medium text-text-primary mb-1">{c.name}</div>
              <div className="font-mono text-xs text-text-secondary">{c.class_code}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Step 2: Select Assignment (Only if Classroom is selected) */}
      {selectedClassroomId && (
        <div className="card-dark p-5 animate-in fade-in slide-in-from-top-4">
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4 flex items-center gap-2">
            <FileTextIcon size={16} /> Select Assignment
          </h3>
          {assignments && assignments.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {assignments.map(a => (
                <button
                  key={a.id}
                  onClick={() => setSelectedAssignmentId(a.id)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    selectedAssignmentId === a.id
                      ? 'bg-accent-teal text-white shadow-md'
                      : 'bg-navy-800 text-text-secondary hover:bg-navy-700 hover:text-text-primary'
                  }`}
                >
                  {a.title}
                </button>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-muted">No assignments available.</p>
          )}
        </div>
      )}

      {/* Step 3: Student Roster (Only if Assignment is selected) */}
      {selectedClassroomId && selectedAssignmentId && (
        <div className="card-dark p-5 animate-in fade-in slide-in-from-top-4">
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4 flex items-center gap-2">
            <UsersIcon size={16} /> Class Roster & Progress
          </h3>
          
          {loadingEnrollments || loadingSubmissions ? (
            <div className="animate-pulse space-y-4">
              <div className="h-10 rounded-lg bg-navy-800" />
              <div className="h-10 rounded-lg bg-navy-800" />
            </div>
          ) : enrollments?.length === 0 ? (
            <EmptyState icon={<UsersIcon size={24} />} title="No Students" message="There are no approved students in this classroom yet." />
          ) : (
            <DataTable 
              headers={['Student', 'Status', 'Latest Score', 'Attempts', 'Action']} 
              rows={studentRoster.map(row => [
                <div key={`student-${row.student.student_id}`}>
                  <p className="font-medium text-sm text-text-primary">{row.student.student_name}</p>
                  <p className="font-mono text-xs text-text-secondary">{row.student.student_roll}</p>
                </div>,
                
                <div key={`status-${row.student.student_id}`}>
                  {row.latestSubmission ? (
                    <StatusBadge status={row.latestSubmission.status} />
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-navy-800 text-text-secondary text-xs font-medium">
                      Not Submitted
                    </span>
                  )}
                </div>,
                
                <span key={`score-${row.student.student_id}`} className="font-mono text-sm font-medium">
                  {row.latestSubmission?.score != null ? (
                    <span className={row.latestSubmission.passed ? 'text-accent-teal' : 'text-status-warning'}>
                      {row.latestSubmission.score.toFixed(1)} / {row.latestSubmission.max_score}
                    </span>
                  ) : (
                    <span className="text-text-muted">—</span>
                  )}
                </span>,
                
                <span key={`attempts-${row.student.student_id}`} className="text-sm text-text-secondary">
                  {row.submissionCount}
                </span>,
                
                <button
                  key={`action-${row.student.student_id}`}
                  onClick={() => setSelectedStudentId(row.student.student_id)}
                  disabled={row.submissionCount === 0}
                  className={`flex items-center gap-1 text-sm font-medium transition-colors ${
                    row.submissionCount > 0 
                      ? 'text-accent-blue hover:text-blue-400 cursor-pointer' 
                      : 'text-navy-600 cursor-not-allowed'
                  }`}
                >
                  View History <ChevronRight size={16} />
                </button>
              ])}
            />
          )}
        </div>
      )}

      {/* Step 4: Student Details Modal */}
      <Modal 
        isOpen={!!selectedStudentId} 
        onClose={() => setSelectedStudentId(null)}
        title={`${selectedStudentName}'s Attempts for ${selectedAssignment?.title}`}
        maxWidth="max-w-4xl"
      >
        {selectedStudentSubmissions.length > 0 ? (
          <div className="space-y-4">
            <DataTable 
              headers={['Attempt', 'Status', 'Score', 'Submitted At']}
              rows={selectedStudentSubmissions.map(s => [
                <span key={`att-${s.id}`} className="font-mono text-xs text-text-primary">#{s.attempt_number}</span>,
                <StatusBadge key={`stat-${s.id}`} status={s.status} />,
                <span key={`scr-${s.id}`} className="font-mono text-sm font-medium">
                  {s.score != null ? (
                    <span className={s.passed ? 'text-accent-teal' : 'text-status-warning'}>
                      {s.score.toFixed(1)} / {s.max_score}
                    </span>
                  ) : (
                    <span className="text-text-muted">—</span>
                  )}
                </span>,
                <span key={`time-${s.id}`} className="text-xs text-text-secondary">{formatDateTime(s.submitted_at)}</span>,
              ])}
            />
          </div>
        ) : (
          <EmptyState icon={<FileTextIcon size={24} />} title="No Attempts" message="No records found for this assignment." />
        )}
      </Modal>
    </div>
  )
}
