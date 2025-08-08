/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    'index.html',
    'src/**/*.{js,jsx,ts,tsx,html}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1E40AF',    // your brand blue
        secondary: '#EF4444',  // your accent red
      },
      spacing: {
        128: '32rem',          // custom spacing utility
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    // add any other Tailwind plugins here
  ],
}

