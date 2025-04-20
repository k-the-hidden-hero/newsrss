/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./newsrss/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        vaporwave: {
          pink: '#FF6AD5',
          purple: '#C774E8',
          blue: '#6A8DFF',
          cyan: '#8BE9FD',
          teal: '#94F8E8',
          neon: '#0FF0FC',
          hotpink: '#F75590',
          orange: '#FFA78B',
          yellow: '#FFEA80',
          dark: '#2C2A4A',
        }
      },
      backgroundImage: {
        'vaporwave-gradient': 'linear-gradient(45deg, #FF6AD5, #C774E8, #6A8DFF, #8BE9FD)',
        'vaporwave-grid': 'radial-gradient(#2C2A4A 1px, transparent 1px)',
      },
      backgroundSize: {
        'grid': '20px 20px',
      }
    },
  },
  plugins: [],
}
