import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

// BUG FIX: Previously only checked token existence.
// A student JWT (role="student") could access the admin portal.
// Now enforces that the role must be "mentor" or "admin".
const ALLOWED_ROLES = ['mentor', 'admin']

export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { token, role } = useAuthStore()

  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (!role || !ALLOWED_ROLES.includes(role)) {
    // Token exists but wrong role — clear it and redirect
    useAuthStore.getState().logout()
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
