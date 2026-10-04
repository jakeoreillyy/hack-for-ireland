<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import { LocateFixed, Minus, Plus } from '@lucide/vue'
import { DESKTOP_QUERY } from '~/lib/map/config'
import { useMapUi } from '~/lib/map/state'

// Talks to the map through shared UI state (useMapUi).
const ui = useMapUi()
const desktop = useMediaQuery(DESKTOP_QUERY, { ssrWidth: 1280 })
const is3D = computed(() => ui.is3D.value ?? desktop.value)

function zoom(delta: number) {
  ui.zoomBy.value = { delta, n: (ui.zoomBy.value?.n ?? 0) + 1 }
}
</script>

<template>
  <div class="flex flex-col items-end gap-2">
    <div class="flex flex-col overflow-hidden rounded-md border-2 border-ink bg-background shadow-[3px_3px_0_var(--ink)]">
      <button type="button" class="grid size-11 place-items-center hover:bg-muted" aria-label="Zoom in" @click="zoom(1)">
        <Plus class="size-4" />
      </button>
      <div class="h-0.5 bg-ink" />
      <button type="button" class="grid size-11 place-items-center hover:bg-muted" aria-label="Zoom out" @click="zoom(-1)">
        <Minus class="size-4" />
      </button>
    </div>
    <button
      type="button"
      class="grid size-11 place-items-center rounded-md border-2 border-ink bg-background text-xs font-bold shadow-[3px_3px_0_var(--ink)] hover:bg-muted"
      :aria-label="is3D ? 'Switch to 2D map' : 'Switch to 3D map'"
      :aria-pressed="is3D"
      @click="ui.is3D.value = !is3D"
    >
      {{ is3D ? '2D' : '3D' }}
    </button>
    <button
      type="button"
      class="grid size-11 place-items-center rounded-md border-2 border-ink bg-background shadow-[3px_3px_0_var(--ink)] hover:bg-muted"
      aria-label="Show all matched applications" title="Show all matched applications"
      @click="ui.recentre.value++"
    >
      <LocateFixed class="size-4" />
    </button>
  </div>
</template>
