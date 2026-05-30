import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'
import { Outlet } from 'react-router-dom'

export const AppShell = () => (
  <div className="flex h-screen overflow-hidden bg-navy-950">
    <Sidebar />
    <div className="flex flex-1 flex-col overflow-hidden">
      <TopNav />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  </div>
)
