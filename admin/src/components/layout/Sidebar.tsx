import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, UserCheck, BookOpen, Activity, FileText,
  Award, ShieldAlert, BarChart3, HeartPulse, Lock, LogOut, ChevronRight,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

interface NavItem {
  label: string
  to: string
  icon: React.ReactNode
  locked?: boolean
}

interface NavGroup {
  group: string
  items: NavItem[]
}

const NAV: NavGroup[] = [
  {
    group: 'OVERVIEW',
    items: [
      { label: 'Dashboard', to: '/dashboard', icon: <LayoutDashboard size={16} /> },
    ],
  },
  {
    group: 'USER GOVERNANCE',
    items: [
      { label: 'Students', to: '/students', icon: <Users size={16} /> },
      { label: 'Mentors', to: '/mentors', icon: <UserCheck size={16} /> },
    ],
  },
  {
    group: 'ASSIGNMENT GOVERNANCE',
    items: [
      { label: 'Assignments', to: '/assignments', icon: <BookOpen size={16} /> },
    ],
  },
  {
    group: 'EVALUATION OVERSIGHT',
    items: [
      { label: 'Sessions & Proofs', to: '/sessions', icon: <Activity size={16} /> },
      { label: 'Results', to: '/results', icon: <FileText size={16} /> },
    ],
  },
  {
    group: 'ISSUANCE',
    items: [
      { label: 'Certificates', to: '/certificates', icon: <Award size={16} />, locked: true },
    ],
  },
  {
    group: 'OBSERVABILITY',
    items: [
      { label: 'Audit Logs', to: '/audit', icon: <ShieldAlert size={16} />, locked: true },
      { label: 'Analytics', to: '/analytics', icon: <BarChart3 size={16} />, locked: true },
      { label: 'Platform Health', to: '/health', icon: <HeartPulse size={16} /> },
    ],
  },
]

export const Sidebar = () => {
  const { logout, username } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col bg-navy-950 border-r border-navy-800">
      {/* Brand */}
      <div className="flex h-16 items-center gap-3 border-b border-navy-800 px-4">
        <img
          src="/logo.png"
          alt="E-Yantra Logo"
          className="h-9 w-9 rounded-xl object-contain shadow-glow-teal"
        />
        <div>
          <p className="font-display text-sm font-bold text-text-primary leading-tight">E-Yantra EEP</p>
          <p className="text-[10px] text-text-secondary tracking-wide uppercase">Admin Control Center</p>
        </div>
      </div>

      {/* Nav */}
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
                    title="Coming in Phase 2"
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
                )
              )}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
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
