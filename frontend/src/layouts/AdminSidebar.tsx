import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, UserCheck, BookOpen, Activity, FileText,
  HeartPulse, Lock, LogOut, ChevronRight, X, Megaphone,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

interface NavItem { label: string; to: string; icon: React.ReactNode; locked?: boolean }
interface NavGroup { group: string; items: NavItem[] }

const NAV: NavGroup[] = [
  {
    group: 'OVERVIEW',
    items: [{ label: 'Dashboard', to: '/admin', icon: <LayoutDashboard size={16} /> }],
  },
  {
    group: 'USER GOVERNANCE',
    items: [
      { label: 'Students', to: '/admin/students', icon: <Users size={16} /> },
      { label: 'Mentors',  to: '/admin/mentors',  icon: <UserCheck size={16} /> },
      { label: 'Announcements', to: '/admin/announcements', icon: <Megaphone size={16} /> },
    ],
  },
  {
    group: 'ASSIGNMENT GOVERNANCE',
    items: [{ label: 'Assignments', to: '/admin/assignments', icon: <BookOpen size={16} /> }],
  },
  {
    group: 'EVALUATION OVERSIGHT',
    items: [
      { label: 'Submissions',       to: '/admin/submissions', icon: <Activity size={16} /> },
      { label: 'Results',           to: '/admin/results',  icon: <FileText size={16} /> },
    ],
  },
  {
    group: 'OBSERVABILITY',
    items: [
      { label: 'Platform Health', to: '/admin/health', icon: <HeartPulse size={16} /> },
    ],
  },
]

export const AdminSidebar = ({ isOpen, onClose }: { isOpen?: boolean, onClose?: () => void }) => {
  const { logout, username } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className={`fixed inset-y-0 left-0 z-50 flex h-screen w-64 shrink-0 flex-col bg-sidebar-bg border-r border-navy-800 transition-transform duration-300 md:relative md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex h-16 items-center gap-3 border-b border-navy-800 px-4">
        <img src="/logo.png" alt="E-Yantra Logo" className="h-9 w-9 rounded-xl object-contain shadow-glow-teal" />
        <div>
          <p className="font-display text-sm font-bold text-text-primary leading-tight">E-Yantra EEP</p>
          <p className="text-[10px] text-text-secondary tracking-wide uppercase">Admin Control Center</p>
        </div>
        {onClose && (
          <button onClick={onClose} className="ml-auto md:hidden text-text-secondary hover:text-text-primary">
            <X size={20} />
          </button>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {NAV.map(({ group, items }) => (
          <div key={group}>
            <p className="mb-1 px-2 text-[10px] font-semibold tracking-widest text-text-secondary uppercase">
              {group}
            </p>
            <div className="space-y-0.5">
              {items.map(({ label, to, icon, locked }) =>
                locked ? (
                  <div
                    key={to}
                    title="Coming soon"
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-text-secondary opacity-40 cursor-not-allowed select-none"
                  >
                    {icon}
                    <span className="text-sm">{label}</span>
                    <Lock size={11} className="ml-auto" />
                  </div>
                ) : (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/admin'}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `relative flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all duration-150 ${
                        isActive
                          ? 'bg-accent-blue/15 text-text-primary font-medium'
                          : 'text-text-secondary hover:text-text-primary hover:bg-navy-900'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <span className="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-0.5 rounded-r bg-accent-blue" />
                        )}
                        {icon}
                        <span>{label}</span>
                        {isActive && <ChevronRight size={12} className="ml-auto text-accent-blue" />}
                      </>
                    )}
                  </NavLink>
                ),
              )}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-navy-800 p-3">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-text-secondary hover:text-status-danger hover:bg-status-danger/10 transition-colors"
        >
          <LogOut size={16} />
          <span>Sign out</span>
          <span className="ml-auto text-xs font-mono truncate max-w-[80px]">{username}</span>
        </button>
      </div>
    </aside>
  )
}
