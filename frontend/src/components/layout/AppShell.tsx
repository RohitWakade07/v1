import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'
import { useAuthStore } from '@/store/authStore'
import { ClassroomJoinGuard } from '@/components/classroom/ClassroomJoinGuard'

export const AppShell = () => {
  const profile = useAuthStore((state) => state.profile)

  const isStudent = profile?.role === 'student'
  const isApproved = profile?.classroom_status === 'APPROVED'

  if (isStudent && !isApproved) {
    return (
      <div className="flex min-h-screen bg-navy-950 text-text-primary">
        <div className="flex min-h-screen flex-1 flex-col overflow-hidden">
          <TopNav />
          <main className="flex-1 overflow-y-auto px-8 py-6 flex items-center justify-center">
            <ClassroomJoinGuard />
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-navy-950 text-text-primary">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col overflow-hidden">
        <TopNav />
        <main className="flex-1 overflow-y-auto px-8 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
