import { Moon, Sun } from 'lucide-react'
import { useThemeStore } from '@/store/themeStore'

export const ThemeToggle = () => {
  const { theme, toggleTheme } = useThemeStore()
  const isDark = theme === 'dark'
  return (
    <button
      id="theme-toggle"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      onClick={toggleTheme}
      className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-navy-800 bg-navy-900 text-text-secondary transition-all duration-200 hover:bg-navy-800/50 hover:text-text-primary hover:border-accent-blue/40"
    >
      <span key={isDark ? 'moon' : 'sun'} className="animate-fade-in" style={{ display: 'flex' }}>
        {isDark ? <Moon size={16} /> : <Sun size={16} />}
      </span>
    </button>
  )
}
