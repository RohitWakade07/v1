import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: 'var(--color-navy-950)',
          900: 'var(--color-navy-900)',
          800: 'var(--color-navy-800)',
        },
        accent: {
          blue: 'var(--color-accent-blue)',
          teal: 'var(--color-accent-teal)',
        },
        surface: {
          light: '#F0F4F8',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          dark: '#1A2D42',
        },
        status: {
          warning: 'var(--color-warning)',
          danger: 'var(--color-danger)',
        },
      },
      fontFamily: {
        display: ['"DM Sans"', 'sans-serif'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        card: '0 10px 22px rgba(6, 10, 15, 0.25)',
        glow: '0 0 16px 2px rgba(46, 134, 193, 0.25)',
        'glow-teal': '0 0 16px 2px rgba(26, 188, 156, 0.25)',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
        fadeInUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          from: { opacity: '0', transform: 'translateX(24px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(46,134,193,0)' },
          '50%': { boxShadow: '0 0 16px 2px rgba(46,134,193,0.25)' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.6s infinite linear',
        'fade-in-up': 'fadeInUp 0.35s ease both',
        'slide-in-right': 'slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1) both',
        'fade-in': 'fadeIn 0.2s ease both',
        'pulse-glow': 'pulseGlow 2.5s ease-in-out infinite',
        'spin-slow': 'spin 2s linear infinite',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}

export default config
