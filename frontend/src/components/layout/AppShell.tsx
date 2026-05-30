import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'

export const AppShell = () => (
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
