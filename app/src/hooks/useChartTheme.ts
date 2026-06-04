import { useEffect, useState } from 'react'
import { getChartTheme } from '@/lib/chartTheme'
import { useThemeStore } from '@/store/themeStore'

export function useChartTheme() {
  const theme = useThemeStore((s) => s.theme)
  const [chartTheme, setChartTheme] = useState(getChartTheme)

  useEffect(() => {
    const frame = requestAnimationFrame(() => setChartTheme(getChartTheme()))
    return () => cancelAnimationFrame(frame)
  }, [theme])

  return chartTheme
}
