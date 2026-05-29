import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0F1923',
          900: '#1A2D42',
          800: '#253545',
        },
        accent: {
          blue: '#2E86C1',
          teal: '#1ABC9C',
        },
        surface: {
          light: '#F0F4F8',
        },
        text: {
          primary: '#E8EDF2',
          secondary: '#8CA0B3',
          dark: '#1A2D42',
        },
        status: {
          warning: '#E67E22',
          danger: '#C0392B',
        },
      },
      fontFamily: {
        display: ['"DM Sans"', 'sans-serif'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        card: '0 10px 22px rgba(6, 10, 15, 0.25)',
      },
    },
  },
  plugins: [],
}

export default config
