import { Outlet } from 'react-router-dom'
import { StudentSidebar } from './StudentSidebar'
import { StudentTopNav } from './StudentTopNav'
import { useAuthStore } from '@/store/authStore'
import { ClassroomJoinGuard } from '@/components/student/classroom/ClassroomJoinGuard'

/** Shell for the student portal. Renders the classroom approval gate
 *  if the student has not yet been approved by a mentor. */
export const StudentLayout = () => {
  const profile = useAuthStore((s) => s.profile)

  const isApproved = profile?.classroom_status === 'APPROVED'

  return (
    <div className="flex h-screen overflow-hidden bg-navy-950 text-text-primary">
      {isApproved && <StudentSidebar />}
      <div className="flex flex-1 flex-col overflow-hidden">
        <StudentTopNav />
        <main className="flex-1 overflow-y-auto px-8 py-6">
          {isApproved ? (
            <Outlet />
          ) : (
            <div className="flex h-full items-center justify-center">
              <ClassroomJoinGuard />
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
