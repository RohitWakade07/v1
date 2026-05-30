import { useEffect } from 'react'
import { AppRouter } from './router/AppRouter.tsx'
import { NotificationToast } from './components/shared/NotificationToast.tsx'
import { useThemeStore } from './store/themeStore'

const App = () => {
  const hydrateTheme = useThemeStore((state) => state.hydrate)

  useEffect(() => {
    hydrateTheme()
  }, [hydrateTheme])

  return (
    <>
      <AppRouter />
      <NotificationToast />
    </>
  )
}

export default App
