<script setup lang="ts">
import GradientOrb from './GradientOrb.vue'
import StageRow, { type StageView } from './StageRow.vue'
import { gsap, reducedMotion } from '~/lib/motion'
import { AUTHORITY_LABEL } from '~/lib/planning/labels'

const pr = usePrecedents()
// One request does both, so the two stages finish together when the answer arrives.
const STAGE_COUNT = 2

const stages = computed<StageView[]>(() => {
  const status: StageView['status'] = pr.state.value === 'done' ? 'done' : 'running'
  const pending: StageView['status'] = pr.state.value === 'done' ? 'done' : 'pending'
  const p = pr.parsed.value
  const r = pr.result.value
  const read = p ? [p.homes ? `${p.homes} homes` : null, p.storeys ? `${p.storeys} storeys` : null, p.mixedUse ? 'mixed use' : null].filter(Boolean).join(', ') : ''
  return [
    {
      stage: 'reading', status,
      label: status === 'done' ? `Read: ${read || 'description'}` : 'Reading your description…',
    },
    {
      stage: 'searching', status: pending,
      label: pending === 'done' && r ? `${r.stats.total} similar applications found` : 'Finding similar applications…',
      detail: r ? AUTHORITY_LABEL[r.proposal.authority] : undefined,
    },
  ]
})

// Progress rail: fills down the stage list as stages finish.
const rail = ref<HTMLElement>()
const doneShare = computed(() => stages.value.filter(s => s.status === 'done').length / STAGE_COUNT)
watch(doneShare, (share) => {
  if (!rail.value) return
  if (reducedMotion()) rail.value.style.transform = `scaleY(${share})`
  else gsap.to(rail.value, { scaleY: share, duration: 0.5, ease: 'power2.out' })
})
</script>

<template>
  <div class="relative overflow-hidden p-5">
    <GradientOrb tone="lavender" :size="300" drift class="-top-28 -right-24" />
    <GradientOrb tone="sky" :size="220" drift class="top-48 -left-28 opacity-60" />
    <p class="type-display-sm relative mb-1 text-foreground">Looking for precedent</p>
    <p class="relative mb-5 text-sm text-muted-foreground">In the national planning register, {{ pr.lastRun.value ? AUTHORITY_LABEL[pr.lastRun.value.authority] : 'Dublin' }}.</p>
    <ol aria-live="polite" class="relative">
      <span aria-hidden="true" class="absolute top-4 bottom-4 left-[9.5px] w-px bg-border" />
      <span ref="rail" aria-hidden="true" class="absolute top-4 bottom-4 left-[9px] w-[2px] origin-top scale-y-0 bg-brand" />
      <StageRow v-for="s in stages" :key="s.stage" :stage="s" />
    </ol>
  </div>
</template>
