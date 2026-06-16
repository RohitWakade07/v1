import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { MentorSidebar } from './MentorSidebar'
import { MentorTopNav } from './MentorTopNav'

export const MentorLayout = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-navy-950">
      <MentorSidebar isOpen={isSidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <MentorTopNav onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto bg-surface-main p-4 md:p-6">
          <Outlet />
        </main>
      </div>

      {isSidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-navy-950/80 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
