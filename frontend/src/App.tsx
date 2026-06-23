import { useEffect } from 'react'
import { AppRouter } from './router/AppRouter.tsx'
import { NotificationToast } from './components/shared/NotificationToast.tsx'
import { useAuthStore } from './store/authStore'
import { useThemeStore } from './store/themeStore'
import { getStudentProfile } from './api/auth'

const App = () => {
  const hydrate = useAuthStore((state) => state.hydrate)
  const hydrateTheme = useThemeStore((state) => state.hydrate)
  const token = useAuthStore((state) => state.token)
  const role = useAuthStore((state) => state.role)
  const profile = useAuthStore((state) => state.profile)
  const setProfile = useAuthStore((state) => state.setProfile)

  useEffect(() => {
    hydrate()
    hydrateTheme()
  }, [hydrate, hydrateTheme])

  useEffect(() => {
    if (token && role === 'student' && !profile) {
      getStudentProfile()
        .then((data) => {
          setProfile(data)
        })
        .catch((err) => {
          console.error('Failed to hydrate student profile:', err)
        })
    }
  }, [token, role, profile, setProfile])

  return (
    <>
      <AppRouter />
      <NotificationToast />
    </>
  )
}

export default App
