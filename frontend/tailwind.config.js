const plugin = require('tailwindcss/plugin')

// Tailwind 3.0 has no logical (RTL-aware) utilities — they arrived in 3.3.
// This plugin provides the same class names (ms-*, pe-*, start-*, text-end …)
// using CSS logical properties so they follow the document direction.
const logicalUtilities = plugin(({ matchUtilities, addUtilities, theme }) => {
  const spacing = theme('spacing')
  const margin = { auto: 'auto', ...spacing }

  matchUtilities({
    ms: (v) => ({ 'margin-inline-start': v }),
    me: (v) => ({ 'margin-inline-end': v }),
  }, { values: margin, supportsNegativeValues: true })

  matchUtilities({
    ps: (v) => ({ 'padding-inline-start': v }),
    pe: (v) => ({ 'padding-inline-end': v }),
  }, { values: spacing })

  matchUtilities({
    start: (v) => ({ 'inset-inline-start': v }),
    end: (v) => ({ 'inset-inline-end': v }),
  }, { values: theme('inset'), supportsNegativeValues: true })

  matchUtilities({
    'border-s': (v) => ({ 'border-inline-start-width': v }),
    'border-e': (v) => ({ 'border-inline-end-width': v }),
  }, { values: theme('borderWidth') })

  matchUtilities({
    'rounded-s': (v) => ({ 'border-start-start-radius': v, 'border-end-start-radius': v }),
    'rounded-e': (v) => ({ 'border-start-end-radius': v, 'border-end-end-radius': v }),
  }, { values: theme('borderRadius') })

  addUtilities({
    '.text-start': { 'text-align': 'start' },
    '.text-end': { 'text-align': 'end' },
    '.float-start': { float: 'inline-start' },
    '.float-end': { float: 'inline-end' },
  })
})

module.exports = {
  presets: [
    require('frappe-ui/src/utils/tailwind.config')
  ],
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [logicalUtilities],
}
