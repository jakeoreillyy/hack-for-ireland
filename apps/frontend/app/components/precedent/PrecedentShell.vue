<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import { Landmark } from '@lucide/vue'
import { DrawerContent, DrawerDescription, DrawerHandle, DrawerPortal, DrawerRoot, DrawerTitle } from 'vaul-vue'
import { ScrollArea } from '~/components/ui/scroll-area'
import MapControls from '~/components/map/MapControls.vue'
import PrecedentMapView from './PrecedentMapView.vue'
import PrecedentPanel from './PrecedentPanel.vue'
import SiteCard from './SiteCard.vue'
import { DESKTOP_QUERY } from '~/lib/map/config'
import { AUTHORITIES, type Authority } from '~/lib/planning/types'

const pr = usePrecedents()

// Share link: each search is mirrored into ?d=&council=&homes=, and a shared link reruns on load.
const route = useRoute()
const router = useRouter()
onMounted(() => {
  const d = typeof route.query.d === 'string' ? route.query.d.trim() : ''
  const council = AUTHORITIES.find(a => a === route.query.council) as Authority | undefined
  const homes = Number(route.query.homes) || null
  if (!d || pr.state.value !== 'idle') return
  useState('pr:form:description').value = d
  if (council) useState('pr:form:authority').value = council
  useState('pr:form:homes').value = homes
  pr.run(d, council ?? 'Dublin City Council', homes)
})
watch(pr.lastRun, (run) => {
  const query = run ? { d: run.description, council: run.authority, ...(run.homes ? { homes: String(run.homes) } : {}) } : {}
  router.replace({ query })
})
const desktop = useMediaQuery(DESKTOP_QUERY, { ssrWidth: 1280 })
const hasCases = computed(() => !!pr.result.value?.cases.length)

// Mobile bottom sheet: peek / half / full. The sheet is 72 px shorter than
// the window so "full" stops below the brand bar; vaul measures px snaps from the top.
const SHEET_TOP_GAP = 72
const SNAP_POINTS: (string | number)[] = [`${148 + SHEET_TOP_GAP}px`, 0.5, 1]
const snap = ref<string | number | null>(1)
// Results and case cards lift the sheet to half height so the map shows the pins.
watch(() => [pr.selectedId.value, pr.state.value], () => {
  if (desktop.value) return
  if (pr.selectedId.value || pr.state.value === 'done') snap.value = 0.5
  else if (pr.state.value === 'idle' || pr.state.value === 'error') snap.value = 1
})
</script>

<template>
  <div class="pr-shell fixed inset-0 overflow-hidden bg-muted">
    <ClientOnly>
      <PrecedentMapView class="pr-noprint" />
    </ClientOnly>

    <!-- Brand bar -->
    <header class="pr-noprint pointer-events-none absolute inset-x-3 top-3 z-20 lg:right-auto lg:left-4 lg:top-4 lg:w-[400px]">
      <div class="pointer-events-auto flex h-12 items-center gap-2.5 rounded-md border-2 border-ink bg-ink px-3 text-white shadow-[3px_3px_0_var(--hivis)]">
        <span class="grid size-7 place-items-center rounded bg-hivis text-ink"><Landmark class="size-4" /></span>
        <span class="font-heading text-[20px] font-black uppercase tracking-wide [font-stretch:72%]">Precedent</span>
        <span class="h-4 w-px bg-white/30" />
        <span class="truncate font-heading text-xs font-bold uppercase tracking-wider text-hivis [font-stretch:85%]">Irish planning decisions</span>
      </div>
    </header>

    <ClientOnly>
      <MapControls class="pr-noprint absolute right-3 z-10 lg:right-4" :class="desktop ? 'bottom-8' : 'top-[72px]'" />

      <div
        v-if="hasCases"
        class="pr-noprint absolute z-10 flex rounded-md border-2 border-ink bg-background text-muted-foreground shadow-[3px_3px_0_var(--ink)]"
        :class="desktop ? 'right-20 bottom-8 flex-col gap-1.5 px-3 py-2 text-xs' : 'left-3 top-[72px] flex-row flex-wrap gap-x-2.5 gap-y-1 px-2 py-1.5 text-[11px] max-w-[calc(100%-80px)]'"
        aria-label="Council decision colours"
      >
        <span v-if="desktop" class="type-caption-upper text-foreground">Council decision</span>
        <span class="flex items-center gap-1.5"><i class="size-2.5 rounded-full bg-planning-granted" /> Granted</span>
        <span class="flex items-center gap-1.5"><i class="size-2.5 rounded-full bg-planning-refused" /> Refused</span>
        <span class="flex items-center gap-1.5"><i class="size-2.5 rounded-full bg-planning-closed" /> Withdrawn or invalid</span>
        <span class="flex items-center gap-1.5"><i class="size-2.5 rounded-full ring-2 ring-planning-appealed ring-inset" /> Appealed</span>
      </div>

      <SiteCard class="pr-noprint absolute z-20" :class="desktop ? 'top-4 left-1/2 -translate-x-1/2' : 'left-3 top-[108px]'" />

      <!-- Desktop: floating side panel -->
      <aside
        v-if="desktop"
        class="pr-panel absolute bottom-4 left-4 top-[76px] z-10 flex w-[400px] flex-col overflow-hidden rounded-md border-2 border-ink bg-background shadow-[4px_4px_0_var(--ink)]"
      >
        <ScrollArea class="h-full">
          <PrecedentPanel />
        </ScrollArea>
      </aside>

      <!-- Mobile: bottom sheet, map stays interactive above it -->
      <DrawerRoot
        v-else
        :open="true"
        :modal="false"
        :dismissible="false"
        :snap-points="SNAP_POINTS"
        v-model:active-snap-point="snap"
      >
        <DrawerPortal>
          <DrawerContent
            class="fixed inset-x-0 bottom-0 z-30 flex h-[calc(100dvh-72px)] flex-col rounded-t-lg border-2 border-b-0 border-ink bg-background shadow-[0_-8px_30px_rgb(0_0_0/0.12)] outline-none"
          >
            <DrawerHandle class="mx-auto mt-2 mb-1 h-1.5 w-12 shrink-0 rounded-full bg-muted-foreground/30" />
            <DrawerTitle class="sr-only">Precedent</DrawerTitle>
            <DrawerDescription class="sr-only">Similar planning applications and their decisions</DrawerDescription>
            <div class="min-h-0 flex-1 overflow-y-auto overscroll-contain" :class="snap === 1 ? '' : 'overflow-hidden'">
              <PrecedentPanel />
            </div>
          </DrawerContent>
        </DrawerPortal>
      </DrawerRoot>
    </ClientOnly>
  </div>
</template>

<style>
/* One-page brief: print the report panel only, full width, on white. */
@media print {
  html, body { height: auto !important; overflow: visible !important; background: #fff !important; }
  .pr-shell { position: static !important; overflow: visible !important; background: #fff !important; }
  .pr-noprint, .pr-panel nav, .pr-panel .print\:hidden { display: none !important; }
  .pr-panel { position: static !important; width: 100% !important; border: 0 !important; box-shadow: none !important; }
  .pr-panel, .pr-panel [data-slot='scroll-area'], .pr-panel [data-slot='scroll-area-viewport'] { overflow: visible !important; max-height: none !important; height: auto !important; }
  .pr-panel svg[role='img'] { max-width: 420px; }
  .pr-panel .sticky { position: static !important; }
  .pr-panel section { break-inside: avoid; }
  .site-notice { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
</style>
