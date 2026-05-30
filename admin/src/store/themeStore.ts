import { create } from 'zustand'

type Theme = 'light' | 'dark'
const STORAGE_KEY = 'sgp.theme'

const applyTheme = (theme: Theme) => {
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark')
  } else {
    document.documentElement.removeAttribute('data-theme')
  }
}

interface ThemeState {
  theme: Theme
  toggleTheme: () => void
  hydrate: () => void
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: 'light',
  toggleTheme: () => {
    const next: Theme = get().theme === 'light' ? 'dark' : 'light'
    localStorage.setItem(STORAGE_KEY, next)
    applyTheme(next)
    set({ theme: next })
  },
  hydrate: () => {
    const saved = localStorage.getItem(STORAGE_KEY) as Theme | null
    const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    const theme = saved ?? preferred
    applyTheme(theme)
    set({ theme })
  },
}))
