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
        // Navigation colors - matching CSS custom properties
        'nav-bg': '#0d1117',
        'nav-hover': 'rgba(0, 255, 255, 0.1)',
        'nav-active': 'rgba(0, 255, 255, 0.2)',
        'nav-border': 'rgba(0, 255, 255, 0.3)',
        'nav-text': '#00ffff',
        'nav-text-dim': 'rgba(0, 255, 255, 0.6)',
      },
      fontFamily: {
        'terminal': ['VT323', 'monospace'],
        'mono': ['IBM Plex Mono', 'monospace'],
      },
      fontSize: {
        'xs': '14px',
        'sm': '16px',
        'base': '20px',
        'lg': '24px',
        'xl': '28px',
        '2xl': '32px',
        '3xl': '36px',
        '4xl': '44px',
        '5xl': '52px',
      },
    },
  },
  plugins: [],
}