import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'

const titles: Record<string, string> = {
  '/': 'Dashboard',
  '/assignments': 'Assignments',
  '/sessions': 'Sessions',
  '/proof/submit': 'Proof Submission',
  '/results': 'Results',
  '/profile': 'Profile',
}

export const AppShell = () => {
  const location = useLocation()
  const title = titles[location.pathname] ?? 'Student Portal'

  return (
    <div className="min-h-screen bg-navy-950 text-text-primary">
      <div className="flex">
        <Sidebar />
        <div className="flex min-h-screen flex-1 flex-col">
          <TopNav title={title} />
          <main className="flex-1 bg-navy-950 px-8 py-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
