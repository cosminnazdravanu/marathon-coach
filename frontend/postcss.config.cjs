// postcss.config.cjs
const tailwindPostcss = require('@tailwindcss/postcss')
const autoprefixer    = require('autoprefixer')

module.exports = {
  plugins: [
    require('postcss-nesting'),   // ← flatten nested rules first
    require('@tailwindcss/postcss'),
    require('autoprefixer'),
  ]
}

