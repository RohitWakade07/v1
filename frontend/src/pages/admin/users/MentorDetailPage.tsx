import { useQuery } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { getMentorDetails, listMentorClassrooms } from '@/api/admin/admin'
import { formatDate } from '@/lib/utils'
import { SkeletonRow } from '@/components/shared/SkeletonCard'

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
      <PageHeader
        title={mentor?.full_name || 'Mentor Details'}
        description={mentor?.email}
      />
      
      <div className="card-dark p-5 mt-6">
        <h3 className="text-lg font-semibold text-text-primary mb-4">Classrooms Created</h3>
        {classroomsLoading ? (
          <div className="space-y-2">
            <SkeletonRow /><SkeletonRow />
          </div>
        ) : (
          <DataTable 
            headers={headers} 
            rows={rows} 
            onRowClick={(index) => navigate(`/admin/classrooms/${classrooms[index].id}`)} 
          />
        )}
      </div>
    </PageWrapper>
  )
}

export default MentorDetailPage
