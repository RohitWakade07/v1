import { useLocation } from 'react-router-dom'
import { ThemeToggle } from '@/components/shared/ThemeToggle'
import { useAuthStore } from '@/store/authStore'
import { ShieldCheck } from 'lucide-react'

const BREADCRUMB_MAP: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/students': 'Students',
  '/mentors': 'Mentors',
  '/assignments': 'Assignments',
  '/sessions': 'Sessions & Proofs',
  '/results': 'Results',
  '/health': 'Platform Health',
}

export const TopNav = () => {
  const { pathname } = useLocation()
  const { username } = useAuthStore()
  const page = BREADCRUMB_MAP[pathname] ?? 'Admin'

  return (
    <header className="flex h-16 items-center justify-between border-b border-navy-800 bg-navy-950 px-6">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-text-secondary">Admin</span>
        <span className="text-navy-800">/</span>
        <span className="font-medium text-text-primary">{page}</span>
      </div>
      <div className="flex items-center gap-3">
        <ThemeToggle />
        <div className="flex items-center gap-2 rounded-lg border border-navy-800 bg-navy-900 px-3 py-1.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent-blue/20 text-accent-blue">
            <ShieldCheck size={14} />
          </div>
          <div className="leading-none">
            <p className="text-xs font-medium text-text-primary">{username || 'Admin'}</p>
            <p className="text-[10px] text-text-secondary uppercase tracking-wide">Admin</p>
          </div>
        </div>
      </div>
    </header>
  )
}
