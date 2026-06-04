import { Outlet } from 'react-router-dom'
import { MentorSidebar } from './MentorSidebar'
import { MentorTopNav } from './MentorTopNav'

export const MentorLayout = () => (
  <div className="flex h-screen overflow-hidden bg-navy-950">
    <MentorSidebar />
    <div className="flex flex-1 flex-col overflow-hidden">
      <MentorTopNav />
      <main className="flex-1 overflow-y-auto bg-surface-main p-6">
        <Outlet />
      </main>
    </div>
  </div>
)
