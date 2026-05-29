import { useEffect } from 'react'
import { AppRouter } from './router/AppRouter.tsx'
import { NotificationToast } from './components/shared/NotificationToast.tsx'
import { useAuthStore } from './store/authStore'

const App = () => {
  const hydrate = useAuthStore((state) => state.hydrate)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  return (
    <>
      <AppRouter />
      <NotificationToast />
    </>
  )
}

export default App
