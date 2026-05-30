import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import { useEffect } from 'react'

export const ProtectedRoute = () => {
  const { isAuthenticated, role } = useAuthStore()
  const location = useLocation()
  const addNotification = useNotificationStore((s) => s.addNotification)

  useEffect(() => {
    if (isAuthenticated && role === 'student') {
      addNotification({
        type: 'error',
        title: 'Unauthorized access',
        message: 'Student accounts cannot access the Mentor Portal.',
      })
    }
  }, [isAuthenticated, role, addNotification])

  if (!isAuthenticated) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />
  }

  if (role === 'student') {
    // If somehow a student JWT is present, force logout or redirect
    useAuthStore.getState().logout()
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
