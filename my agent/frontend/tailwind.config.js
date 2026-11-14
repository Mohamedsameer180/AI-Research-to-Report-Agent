/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#050505',
          secondary: '#0A0A0A',
          card: '#101010',
          elevated: '#151515',
        },
        accent: {
          DEFAULT: '#FF6A00',
          bright: '#FF8A00',
          dark: '#CC5500',
          glow: 'rgba(255, 106, 0, 0.25)',
        },
        border: {
          subtle: 'rgba(255, 255, 255, 0.08)',
          glow: 'rgba(255, 106, 0, 0.3)',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#A1A1AA',
          muted: '#71717A',
        },
        status: {
          success: '#10B981',
          warning: '#FF8A00',
          error: '#EF4444',
          idle: '#71717A',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'orange-glow': '0 0 25px rgba(255, 106, 0, 0.25)',
        'orange-glow-lg': '0 0 50px rgba(255, 106, 0, 0.35)',
        'orange-glow-sm': '0 0 12px rgba(255, 106, 0, 0.2)',
      },
      animation: {
        'spin-slow': 'spin 12s linear infinite',
        'spin-reverse-slow': 'spinReverse 16s linear infinite',
        'pulse-glow': 'pulseGlow 2.5s ease-in-out infinite',
        'pulse-fast': 'pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        spinReverse: {
          '0%': { transform: 'rotate(360deg)' },
          '100%': { transform: 'rotate(0deg)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.9', transform: 'scale(1.05)' },
        }
      }
    },
  },
  plugins: [],
}
