<script setup lang="ts">
import { MapPin, X } from '@lucide/vue'
import { percent } from '~/lib/planning/labels'

// "Drop your site": the predictor's figures within a few km of the tapped point, and faster nearby areas.
const pr = usePrecedents()
const site = computed(() => pr.site.value)
const faster = computed(() => (site.value?.alternatives ?? []).filter(a => a.weeksSaved > 0).slice(0, 2))
</script>

<template>
  <div v-if="site" class="w-[300px] max-w-[calc(100vw-24px)] rounded-md border-2 border-ink bg-background p-3 shadow-[3px_3px_0_var(--ink)]" role="status" aria-live="polite">
    <div class="flex items-center justify-between gap-2">
      <p class="type-caption-upper flex items-center gap-1.5 text-foreground"><MapPin class="size-3.5" /> Your site</p>
      <button type="button" class="grid size-7 place-items-center rounded text-muted-foreground hover:bg-muted" aria-label="Remove site" @click="pr.clearSite()"><X class="size-4" /></button>
    </div>

    <p v-if="site.loading" class="mt-1 text-sm text-muted-foreground">Looking at similar applications nearby…</p>
    <p v-else-if="site.error" class="mt-1 text-sm text-muted-foreground">{{ site.error }}</p>
    <template v-else-if="site.estimate">
      <p class="mt-1 text-sm text-foreground">
        Within {{ site.estimate.radiusKm }} km: <strong>{{ site.estimate.total }} similar</strong>, typically <strong>{{ site.estimate.medianWeeks }} weeks</strong>, <strong>{{ percent(site.estimate.grantRate) }} granted</strong>
      </p>
      <ul v-if="site.warnings.length" class="mt-1.5 space-y-0.5 text-xs text-muted-foreground">
        <li v-for="w in site.warnings" :key="w">{{ w }}</li>
      </ul>
      <div v-if="faster.length" class="mt-2 space-y-1 border-t pt-2">
        <p class="text-xs font-semibold text-muted-foreground">Faster nearby</p>
        <button
          v-for="a in faster"
          :key="a.label"
          type="button"
          class="flex w-full items-baseline justify-between gap-2 rounded px-1 py-0.5 text-left text-xs hover:bg-hivis/40"
          :title="`${a.total} similar · ${percent(a.grantRate)} granted · ${a.distanceKm} km ${a.direction}`"
          @click="pr.dropSite(a.coordinates[0], a.coordinates[1])"
        >
          <span class="truncate text-foreground">{{ a.label }}</span>
          <span class="shrink-0 font-semibold tabular-nums text-foreground">{{ a.weeksSaved }} wks faster</span>
        </button>
      </div>
    </template>
    <p class="mt-2 text-[11px] text-muted-foreground">Team planning predictor · past decisions, not a forecast</p>
  </div>
</template>
