<script setup lang="ts">
import { CalendarDays, ExternalLink, Home, Layers, MapPin, PersonStanding } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import PanelHeader from './PanelHeader.vue'
import { day } from '~/lib/format'
import type { PlanningCase } from '~/lib/planning/types'
import { AUTHORITY_LABEL, STATUS_STYLE, weeksLabel } from '~/lib/planning/labels'

const props = defineProps<{ item: PlanningCase }>()
const pr = usePrecedents()
// Dublin City cases have no link in the register; resolve one from the council portal.
const link = ref<string | null>(props.item.link)
const resolving = ref(false)
watch(() => props.item.id, async () => {
  link.value = props.item.link
  if (link.value || props.item.authority !== 'Dublin City Council') return
  resolving.value = true
  const id = props.item.id
  const url = await councilLink(props.item)
  if (props.item.id === id) link.value = url
  resolving.value = false
}, { immediate: true })
const streetView = computed(() => props.item.coordinates && `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${props.item.coordinates[1]},${props.item.coordinates[0]}`)
</script>

<template>
  <div>
    <PanelHeader :title="item.title" :subtitle="item.id" @back="pr.selectCase(null)" />

    <div class="space-y-5 p-5">
      <div class="flex flex-wrap items-center gap-2">
        <span class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold" :class="STATUS_STYLE[item.status].soft">
          <i class="size-2 rounded-full" :class="STATUS_STYLE[item.status].dot" /> {{ item.decisionLabel }}
        </span>
        <span v-if="item.appealed" class="rounded-full border border-planning-appealed/30 bg-planning-appealed/10 px-2.5 py-1 text-xs font-semibold text-planning-appealed">Appealed</span>
        <span v-if="item.furtherInfo" class="rounded-full border px-2.5 py-1 text-xs font-semibold text-muted-foreground">Further info requested</span>
      </div>

      <div class="space-y-1">
        <p class="flex items-start gap-1.5 text-sm text-foreground" :title="item.location"><MapPin class="mt-0.5 size-4 shrink-0 text-brand" /> <span class="line-clamp-2">{{ item.location || 'Address not recorded' }}</span></p>
        <p class="pl-[22px] text-xs text-muted-foreground">{{ AUTHORITY_LABEL[item.authority] }}</p>
      </div>

      <dl class="grid grid-cols-2 gap-px overflow-hidden rounded-xl border bg-border text-sm">
        <div class="bg-background p-3">
          <dt class="flex items-center gap-1 text-xs text-muted-foreground"><Home class="size-3" /> Homes</dt>
          <dd class="type-title text-foreground tabular-nums">{{ item.homes ?? 'Not stated' }}</dd>
        </div>
        <div class="bg-background p-3">
          <dt class="flex items-center gap-1 text-xs text-muted-foreground"><Layers class="size-3" /> Storeys</dt>
          <dd class="type-title text-foreground tabular-nums">{{ item.storeys ?? 'Not stated' }}</dd>
        </div>
        <div class="bg-background p-3">
          <dt class="flex items-center gap-1 text-xs text-muted-foreground"><CalendarDays class="size-3" /> Received</dt>
          <dd class="font-medium tabular-nums">{{ item.receivedDate ? day(item.receivedDate) : 'Not recorded' }}</dd>
        </div>
        <div class="bg-background p-3">
          <dt class="text-xs text-muted-foreground">Time to decision</dt>
          <dd class="font-medium tabular-nums">{{ weeksLabel(item) }}</dd>
        </div>
      </dl>

      <div class="space-y-2">
        <Button v-if="link" as-child class="h-11 w-full rounded-md btn-hivis bg-hivis text-ink hover:bg-hivis text-[15px]">
          <a :href="link" target="_blank" rel="noopener"><ExternalLink class="size-4" /> Open council record</a>
        </Button>
        <Button v-else-if="resolving" disabled class="h-11 w-full rounded-md btn-hivis bg-hivis text-ink hover:bg-hivis text-[15px]">
          <ExternalLink class="size-4" /> Finding council record…
        </Button>
        <p v-else class="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
          Search <strong class="font-mono text-foreground">{{ item.id }}</strong> on the council's planning site. We couldn't find a direct link for this case.
        </p>
        <Button v-if="streetView" as-child variant="outline" class="h-10 w-full rounded-md border-2 border-ink">
          <a :href="streetView" target="_blank" rel="noopener"><PersonStanding class="size-4" /> Street View</a>
        </Button>
      </div>

      <p class="text-[11px] leading-relaxed text-muted-foreground">National Planning Applications register · {{ item.id }}</p>
    </div>
  </div>
</template>
