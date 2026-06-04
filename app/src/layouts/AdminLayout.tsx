import { Outlet } from 'react-router-dom'
import { AdminSidebar } from './AdminSidebar'
import { AdminTopNav } from './AdminTopNav'

export const AdminLayout = () => (
  <div className="flex h-screen overflow-hidden bg-navy-950">
    <AdminSidebar />
    <div className="flex flex-1 flex-col overflow-hidden">
      <AdminTopNav />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  </div>
)
