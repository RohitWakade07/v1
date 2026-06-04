/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: ['selector', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        'navy-950': 'var(--color-navy-950)',
        'navy-900': 'var(--color-navy-900)',
        'navy-850': 'var(--color-navy-850)',
        'navy-800': 'var(--color-navy-800)',
        'navy-700': 'var(--color-navy-700)',
        'accent-blue': 'var(--color-accent-blue)',
        'accent-teal': 'var(--color-accent-teal)',
        'status-warning': 'var(--color-warning)',
        'status-danger': 'var(--color-danger)',
        'surface-main': 'var(--color-surface-main)',
        'surface-inset': 'var(--color-surface-inset)',
        'sidebar-bg': 'var(--color-sidebar-bg)',
        'input-bg': 'var(--color-input-bg)',
        'input-border': 'var(--color-input-border)',
        /* @deprecated use surface-main — kept for gradual migration */
        'surface-light': 'var(--color-surface-main)',
      },
      textColor: {
        'text-primary': 'var(--color-text-primary)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-muted': 'var(--color-text-muted)',
        'text-disabled': 'var(--color-text-disabled)',
      },
      fontFamily: {
        display: ['DM Sans', 'sans-serif'],
        sans: ['IBM Plex Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        card: 'var(--shadow-card)',
        'card-hover': 'var(--shadow-card-hover)',
        glow: '0 0 20px rgba(46,134,193,0.2)',
        'glow-teal': '0 0 20px rgba(26,188,156,0.2)',
      },
    },
  },
  plugins: [],
}
