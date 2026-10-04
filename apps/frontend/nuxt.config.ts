// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['shadcn-nuxt'],
  css: ['~/assets/css/main.css'],
  vite: {
    plugins: [tailwindcss()],
  },
  shadcn: {
    prefix: '',
    componentDir: './app/components/ui',
  },
  runtimeConfig: {
    public: {
      // The planning predictor API (apps/backend). Override with NUXT_PUBLIC_API_BASE.
      apiBase: 'http://127.0.0.1:8000',
    },
  },
  app: {
    head: {
      title: 'Precedent · Irish planning decisions',
      meta: [{ name: 'description', content: 'See how similar housing proposals fared in planning, from the national planning register.' }],
    },
  },
  typescript: { strict: true },
})
