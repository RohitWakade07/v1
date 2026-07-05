import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { Pagination } from '@/components/shared/Pagination'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { getClassroomDetails, listClassroomStudents, listClassroomSessions } from '@/api/admin/admin'
import { formatDate } from '@/lib/utils'
import { SkeletonRow } from '@/components/shared/SkeletonCard'

export const ClassroomDetailPage = () => {
  const { classroomId } = useParams<{ classroomId: string }>()
  const navigate = useNavigate()
  
  const [activeTab, setActiveTab] = useState<'students' | 'sessions'>('students')
  const [studentPage, setStudentPage] = useState(1)
  const [sessionPage, setSessionPage] = useState(1)

  const { data: classroom } = useQuery({
    queryKey: ['admin-classroom', classroomId],
    queryFn: () => getClassroomDetails(classroomId!),
    enabled: !!classroomId
  })

  const { data: studentsResponse, isLoading: studentsLoading } = useQuery({
    queryKey: ['admin-classroom-students', classroomId, studentPage],
    queryFn: () => listClassroomStudents(classroomId!, studentPage, 20),
    enabled: activeTab === 'students' && !!classroomId
  })

  const { data: sessionsResponse, isLoading: sessionsLoading } = useQuery({
    queryKey: ['admin-classroom-sessions', classroomId, sessionPage],
    queryFn: () => listClassroomSessions(classroomId!, sessionPage, 20),
    enabled: activeTab === 'sessions' && !!classroomId
  })

  const students = studentsResponse?.data || []
  const studentPages = studentsResponse?.pages || 1

  const sessions = sessionsResponse?.data || []
  const sessionPages = sessionsResponse?.pages || 1

  const studentHeaders = ['Roll Number', 'Full Name', 'Email', 'Joined']
  const studentRows = students.map(s => [
    <span key="roll" className="font-mono text-sm text-text-secondary">{s.roll_number}</span>,
    <span key="name" className="font-medium text-text-primary">{s.full_name}</span>,
    <span key="email" className="text-sm text-text-secondary">{s.email}</span>,
    <span key="date" className="text-sm text-text-secondary">{formatDate(s.created_at)}</span>,
  ])

  const sessionHeaders = ['Student', 'Assignment', 'Status', 'Started', 'Score']
  const sessionRows = sessions.map(s => [
    <span key="student" className="font-medium text-text-primary">{s.student_name}</span>,
    <span key="assignment" className="text-sm text-text-secondary">{s.assignment_title}</span>,
    <span key="status"><StatusBadge status={s.status as any} /></span>,
    <span key="started" className="text-sm text-text-secondary">{formatDate(s.started_at)}</span>,
    <span key="score" className="font-mono">{s.final_score ?? '-'}</span>,
  ])

  return (
    <PageWrapper>
      <div className="mb-4 text-sm text-text-secondary">
        <button onClick={() => navigate(-1)} className="hover:text-text-primary underline">Back</button>
        {' > '} {classroom?.name || 'Classroom Details'}
      </div>
      <PageHeader
        title={classroom?.name || 'Classroom Details'}
        description={`Join Code: ${classroom?.join_code || '---'}`}
      />
      
      <div className="card-dark p-5 mt-6">
        <div className="flex space-x-6 border-b border-navy-800 mb-6">
          <button 
            className={`pb-3 font-medium transition-colors ${activeTab === 'students' ? 'text-accent-blue border-b-2 border-accent-blue' : 'text-text-secondary hover:text-text-primary'}`}
            onClick={() => setActiveTab('students')}
          >
            Enrolled Students
          </button>
          <button 
            className={`pb-3 font-medium transition-colors ${activeTab === 'sessions' ? 'text-accent-blue border-b-2 border-accent-blue' : 'text-text-secondary hover:text-text-primary'}`}
            onClick={() => setActiveTab('sessions')}
          >
            Sessions & Results
          </button>
        </div>

        {activeTab === 'students' && (
          <div>
            {studentsLoading ? (
              <div className="space-y-2"><SkeletonRow /><SkeletonRow /></div>
            ) : (
              <>
                <DataTable headers={studentHeaders} rows={studentRows} />
                <Pagination page={studentPage} totalPages={studentPages} onPageChange={setStudentPage} className="mt-4" />
              </>
            )}
          </div>
        )}

        {activeTab === 'sessions' && (
          <div>
            {sessionsLoading ? (
              <div className="space-y-2"><SkeletonRow /><SkeletonRow /></div>
            ) : (
              <>
                <DataTable headers={sessionHeaders} rows={sessionRows} />
                <Pagination page={sessionPage} totalPages={sessionPages} onPageChange={setSessionPage} className="mt-4" />
              </>
            )}
          </div>
        )}
      </div>
    </PageWrapper>
  )
}

export default ClassroomDetailPage
