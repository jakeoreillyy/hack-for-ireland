<script setup lang="ts">
import PrecedentShell from '~/components/precedent/PrecedentShell.vue'

useHead({
  title: 'Precedent · Irish planning decisions',
  meta: [{ name: 'description', content: 'See how similar housing proposals fared in planning, from the national planning register.' }],
  // Archivo's condensed widths set the site-notice lettering.
  link: [
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
    { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&display=swap' },
  ],
})
</script>

<template>
  <PrecedentShell />
</template>
