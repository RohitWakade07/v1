import { useEffect } from 'react'
import { AppRouter } from '@/router/AppRouter'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore } from '@/store/themeStore'

function App() {
  const { hydrate: hydrateAuth } = useAuthStore()
  const { hydrate: hydrateTheme } = useThemeStore()

  useEffect(() => {
    hydrateAuth()
    hydrateTheme()
  }, [hydrateAuth, hydrateTheme])

  return <AppRouter />
}

export default App
