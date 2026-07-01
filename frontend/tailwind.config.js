/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f2f9f5',
          100: '#e1f2e8',
          200: '#c5e4d2',
          300: '#9acfbd',
          400: '#68b19e',
          500: '#469683',
          600: '#347869',
          700: '#2a6055',
          800: '#234e45',
          900: '#1d413b',
        }
      }
    },
  },
  plugins: [],
}
