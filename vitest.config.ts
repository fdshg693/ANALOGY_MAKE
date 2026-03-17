import { defineConfig } from 'vitest/config'
import { resolve } from 'path'

export default defineConfig({
  test: {
    environment: 'node',
  },
  resolve: {
    alias: {
      '~': resolve(__dirname, '.'),
    },
  },
  define: {
    'import.meta.client': 'globalThis.__NUXT_CLIENT__',
  },
})
