// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui'
  ],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || ''
    }
  },

  // Proxy /api requests to the FastAPI backend.
  // This keeps cookies on the same origin (localhost:3000) so httpOnly
  // cookies and CSRF tokens work correctly.
  routeRules: {
    '/api/**': {
      proxy: 'http://localhost:8000/api/**'
    }
  },

  compatibilityDate: '2025-01-15',

  colorMode: {
    preference: 'system',
    fallback: 'light',
    classSuffix: '',
    storageKey: 'nagare-color-mode',
    dataValue: 'theme'
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})
