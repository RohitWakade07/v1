/** Reads chart colors from CSS custom properties (theme-aware). */
export function getChartTheme() {
  const root = document.documentElement
  const get = (name: string) =>
    getComputedStyle(root).getPropertyValue(name).trim()

  return {
    grid: get('--color-chart-grid'),
    axis: get('--color-chart-axis'),
    tooltip: {
      backgroundColor: get('--color-chart-tooltip-bg'),
      borderColor: get('--color-chart-tooltip-border'),
      color: get('--color-chart-tooltip-text'),
      borderRadius: '8px',
    },
    cursor: { fill: get('--color-chart-cursor') },
    barPrimary: get('--color-accent-blue'),
    barSecondary: get('--color-accent-teal'),
  }
}
