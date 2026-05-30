import { Sun, Moon } from 'lucide-react'
import { useThemeStore } from '@/store/themeStore'

export const ThemeToggle = () => {
  const { theme, toggleTheme } = useThemeStore()
  return (
    <button
      onClick={toggleTheme}
      title={theme === 'dark' ? 'Switch to light' : 'Switch to dark'}
      className="flex h-9 w-9 items-center justify-center rounded-lg border border-navy-800 bg-navy-900 text-text-secondary hover:text-text-primary hover:border-accent-blue transition-all duration-150"
    >
      {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  )
}
