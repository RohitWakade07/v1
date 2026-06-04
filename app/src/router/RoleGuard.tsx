import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import type { UserRole } from '@/types/api'

interface RoleGuardProps {
  allowedRoles: UserRole[]
  redirectTo?: string
}

/** Protects a route subtree by role.
 *  - Unauthenticated → redirect to /login
 *  - Wrong role → redirect to their own home (or 403 page) */
export const RoleGuard = ({ allowedRoles, redirectTo = '/login' }: RoleGuardProps) => {
  const { isAuthenticated, role } = useAuthStore()

  if (!isAuthenticated) {
    const current = window.location.pathname + window.location.search
    return <Navigate to={`/login?redirect=${encodeURIComponent(current)}`} replace />
  }

  if (!role || !allowedRoles.includes(role)) {
    // Route to the correct home for their role rather than a dead end
    if (role === 'student') return <Navigate to="/student" replace />
    if (role === 'mentor') return <Navigate to="/mentor" replace />
    if (role === 'admin') return <Navigate to="/admin" replace />
    return <Navigate to={redirectTo} replace />
  }

  return <Outlet />
}
