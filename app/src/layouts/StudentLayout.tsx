import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { StudentSidebar } from './StudentSidebar'
import { StudentTopNav } from './StudentTopNav'
import { useAuthStore } from '@/store/authStore'
import { ClassroomJoinGuard } from '@/components/student/classroom/ClassroomJoinGuard'

/** Shell for the student portal. Renders the classroom approval gate
 *  if the student has not yet been approved by a mentor. */
export const StudentLayout = () => {
  const profile = useAuthStore((s) => s.profile)
  const [isSidebarOpen, setSidebarOpen] = useState(false)

  const isApproved = profile?.classroom_status === 'APPROVED'

  return (
    <div className="flex h-screen overflow-hidden bg-navy-950 text-text-primary">
      {isApproved && <StudentSidebar isOpen={isSidebarOpen} onClose={() => setSidebarOpen(false)} />}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <StudentTopNav onMenuClick={isApproved ? () => setSidebarOpen(true) : undefined} />
        <main className="flex-1 overflow-y-auto px-4 md:px-8 py-6">
          {isApproved ? (
            <Outlet />
          ) : (
            <div className="flex h-full items-center justify-center">
              <ClassroomJoinGuard />
            </div>
          )}
        </main>
      </div>
      
      {isApproved && isSidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-navy-950/80 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
