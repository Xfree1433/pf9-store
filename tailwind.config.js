/** @type {import('tailwindcss').Config} */
// Brand theme (2026-11): "cashmere counter, dark ledger" — adapted from the
// Mollie style on Refero Styles. Warm oat paper, espresso ink, ledger-brown
// pill buttons, copper accent. The stock palettes below are re-tuned in place
// so every existing utility class (gray-*, blue-*, green-*, ...) picks up the
// new look without touching page markup.

module.exports = {
  // Root pages plus the sub-folder pages that also load dist/tailwind.css.
  // templates/ is a public lead-magnet folder with its own inline CSS — left out on purpose.
  content: [
    './*.html',
    './comparisons/**/*.html',
    './glossary/**/*.html',
    './lead-magnets/**/*.html',
    './refer/**/*.html',
    './tools/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        // Warm "oat" neutrals in place of cool gray.
        gray: {
          50: '#f7f4f1',
          100: '#efe9e3',
          200: '#e3dbd2',
          300: '#d1c6ba',
          400: '#8f8275',
          500: '#76695e',
          600: '#5a4e45',
          700: '#443931',
          800: '#2f2620',
          900: '#211812',
          950: '#150e0a',
        },
        black: '#1a120d',
        // Manufacturing — muted steel blue
        blue: {
          50: '#eef3f6', 100: '#dce6ec', 200: '#bccfda', 300: '#94b1c1', 400: '#6a90a5',
          500: '#4c748b', 600: '#3b5d72', 700: '#2f4a5c', 800: '#263c4b', 900: '#1f313d',
        },
        indigo: {
          50: '#eef3f6', 100: '#dce6ec', 200: '#bccfda', 300: '#94b1c1', 400: '#6a90a5',
          500: '#4c748b', 600: '#3b5d72', 700: '#2f4a5c', 800: '#263c4b', 900: '#1f313d',
        },
        // Property — ledger green (Mollie "Active Green")
        green: {
          50: '#eff5ec', 100: '#dcebd6', 200: '#b9d6ae', 300: '#8fbd80', 400: '#5f9e4e',
          500: '#3b8530', 600: '#288a26', 700: '#1e681d', 800: '#1a5219', 900: '#153f15',
        },
        // Operations — muted plum
        purple: {
          50: '#f5f0f3', 100: '#ebe0e7', 200: '#d6c1cf', 300: '#bb9cb1', 400: '#9a7290',
          500: '#7f5876', 600: '#694761', 700: '#563a50', 800: '#452f40', 900: '#382734',
        },
        // AI / highlights — copper (Mollie "Copper Link")
        amber: {
          50: '#fcf3ec', 100: '#f8e4d4', 200: '#f0c6a6', 300: '#e9a371', 400: '#e5853f',
          500: '#e07122', 600: '#c45e17', 700: '#a14c14', 800: '#7f3c12', 900: '#5f2e0f',
        },
        ledger: '#3b281d',
        copper: '#e07122',
        oat: '#f7f4f1',
        espresso: '#211006',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      borderRadius: {
        xl: '1rem',
        '2xl': '1.5rem',
      },
    },
  },
  plugins: [],
};
