/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'terminal-bg': '#14192f',
        'terminal-dark': '#0d0d0d',
        'terminal-cyan': '#00ffff',
        'terminal-green': '#00ff00',
        'terminal-amber': '#ffbf00',
        'commodore-orange': '#ff8c1a',
        'commodore-purple': '#b967ff',
        'success-green': '#00FF00',
        'error-pink': '#FF0080',
        'warning-gold': '#FFD700',
        'processing-blue': '#00BFFF',
      },
      fontFamily: {
        'terminal': ['VT323', 'monospace'],
        'mono': ['IBM Plex Mono', 'monospace'],
      },
      fontSize: {
        'base': '18px',
        'lg': '20px',
        'xl': '24px',
        '2xl': '28px',
        '3xl': '32px',
        '4xl': '40px',
      },
    },
  },
  plugins: [],
}