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
  // Server-only. Set in .env; never expose under `public`.
  runtimeConfig: {
    // Team predictor (hack-for-ireland apps/backend). Empty = use the local snapshot only.
    predictorUrl: '',
  },
  app: {
    head: {
      title: 'Precedent · Dublin Planning Explorer',
      meta: [{ name: 'description', content: 'Explore illustrative planning applications and the evidence behind comparable decisions.' }],
    },
  },
  typescript: { strict: true },
})
