import { useEffect } from 'react'
import { AppRouter } from './router/AppRouter.tsx'
import { NotificationToast } from './components/shared/NotificationToast.tsx'
import { useAuthStore } from './store/authStore'
import { useThemeStore } from './store/themeStore'

const App = () => {
  const hydrate = useAuthStore((state) => state.hydrate)
  const hydrateTheme = useThemeStore((state) => state.hydrate)

  useEffect(() => {
    hydrate()
    hydrateTheme()
  }, [hydrate, hydrateTheme])

  return (
    <>
      <AppRouter />
      <NotificationToast />
    </>
  )
}

export default App
