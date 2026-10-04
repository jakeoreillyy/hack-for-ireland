<script setup lang="ts">
import { ChevronDown, Link2, Printer } from '@lucide/vue'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import PanelHeader from '~/components/property/PanelHeader.vue'
import { gsap, reducedMotion } from '~/lib/motion'
import { SNAPSHOT_AUTHORITIES, type Authority, type PrecedentsResponse } from '~/lib/planning/contract'
import { AUTHORITY_LABEL, STATUS_STYLE, percent } from '~/lib/planning/labels'

// One question, one answer, five cases.
const props = defineProps<{ animate?: boolean }>()
const pr = usePrecedents()
const result = computed(() => pr.result.value!)
const stats = computed(() => result.value.stats)
const explanation = computed(() => pr.explanation.value)
const council = computed(() => AUTHORITY_LABEL[result.value.proposal.authority])
const title = computed(() => {
  const p = result.value.proposal
  return [p.homes ? `${p.homes} homes` : null, p.storeys ? `${p.storeys} storeys` : null, p.mixedUse ? 'mixed use' : null].filter(Boolean).join(' · ') || p.kind
})
const snapshot = computed(() => new Date(result.value.source.snapshotDate).toLocaleDateString('en-IE', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }))

const subline = computed(() => {
  const parts = [`${stats.value.total} similar`]
  if (stats.value.medianWeeks != null) parts.push(`typically ${stats.value.medianWeeks} weeks to a decision`)
  return parts.join(' · ')
})

// "What added time": the predictor's delay factors, with the matching share folded in.
const delays = computed(() => (result.value.delayFactors ?? []).filter(f => f.addedWeeks > 0).map((f) => {
  const share = f.factor === 'appeal' ? stats.value.appealShare : stats.value.furtherInfoShare
  return { key: f.factor, label: f.label, weeks: f.addedWeeks, share }
}))

function printBrief() {
  window.print()
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    toast('Link copied', { description: 'Opens this search on the current data.' })
  } catch {
    toast('Copy the link from the address bar')
  }
}

// Other councils, on request: the same proposal sent to each (one /api/precedents call per council).
type CompareRow = { authority: Authority; stats: PrecedentsResponse['stats'] | null }
const compareOpen = ref(false)
const compareRows = ref<CompareRow[] | null>(null)
watch(() => pr.result.value, () => { compareRows.value = null; compareOpen.value = false })
async function toggleCompare() {
  compareOpen.value = !compareOpen.value
  if (!compareOpen.value || compareRows.value) return
  const p = result.value.proposal
  // The four Dublin councils, plus this one if it's elsewhere: at most five searches.
  const councils = SNAPSHOT_AUTHORITIES.includes(p.authority) ? [...SNAPSHOT_AUTHORITIES] : [p.authority, ...SNAPSHOT_AUTHORITIES]
  compareRows.value = await Promise.all(councils.map(async (authority): Promise<CompareRow> => {
    if (authority === p.authority) return { authority, stats: stats.value }
    try {
      const query: Record<string, string | number | boolean> = { authority, homes: p.homes ?? 0, mixedUse: p.mixedUse }
      if (p.storeys) query.storeys = p.storeys
      return { authority, stats: (await $fetch<PrecedentsResponse>('/api/precedents', { query })).stats }
    } catch {
      return { authority, stats: null }
    }
  }))
}
function openCouncil(authority: Authority) {
  const last = pr.lastRun.value
  if (!last || authority === result.value.proposal.authority) return
  useState<Authority>('pr:form:authority').value = authority
  pr.run(last.description, authority, last.homes)
}

const root = ref<HTMLElement>()
onMounted(() => {
  if (!props.animate || !root.value || reducedMotion()) return
  gsap.from(root.value.querySelectorAll('[data-rise]'), { y: 14, autoAlpha: 0, duration: 0.45, stagger: 0.07, ease: 'power3.out', clearProps: 'all' })
})
</script>

<template>
  <div ref="root">
    <PanelHeader :title="title" :subtitle="council" @back="pr.reset()">
      <template #actions>
        <Button size="icon" variant="ghost" class="size-9 shrink-0 print:hidden" aria-label="Copy link to this search" title="Copy link" @click="copyLink"><Link2 class="size-4" /></Button>
        <Button size="icon" variant="ghost" class="size-9 shrink-0 print:hidden" aria-label="Print" title="Print" @click="printBrief"><Printer class="size-4" /></Button>
      </template>
    </PanelHeader>

    <div class="space-y-7 px-5 py-6">
      <!-- Headline -->
      <section data-rise class="space-y-2">
        <h2 v-if="stats.grantRate != null" class="type-display-md text-balance text-foreground">
          <span class="tabular-nums">{{ percent(stats.grantRate) }}</span> of decided similar applications were granted
        </h2>
        <h2 v-else class="type-display-sm text-balance text-foreground">Too few decided applications to give a grant rate</h2>
        <p class="text-sm text-muted-foreground">{{ subline }}</p>
        <ul v-if="result.warnings?.length" class="space-y-0.5 text-xs text-muted-foreground">
          <li v-for="w in result.warnings" :key="w">{{ w }}</li>
        </ul>
      </section>

      <!-- In plain English -->
      <section v-if="explanation" data-rise class="space-y-2">
        <h3 class="type-caption-upper text-muted-foreground">In plain English</h3>
        <p class="text-sm leading-relaxed text-foreground">{{ explanation.text }}</p>
      </section>

      <!-- What added time -->
      <section v-if="delays.length" data-rise class="space-y-2">
        <h3 class="type-caption-upper text-muted-foreground">What added time</h3>
        <ul class="divide-y rounded-lg border text-sm">
          <li v-for="d in delays" :key="d.key" class="flex items-baseline justify-between gap-3 px-3 py-2.5">
            <span class="text-foreground">{{ d.label }}<span v-if="d.share != null" class="text-muted-foreground"> · {{ percent(d.share) }} of cases</span></span>
            <span class="shrink-0 font-semibold text-foreground tabular-nums">+{{ d.weeks }} wks</span>
          </li>
        </ul>
        <p class="text-xs text-muted-foreground">Typical extra time when this happened. A comparison, not a cause.</p>
      </section>

      <!-- Closest matches -->
      <section data-rise class="space-y-2">
        <h3 class="type-caption-upper text-muted-foreground">Closest matches</h3>
        <ul class="divide-y rounded-lg border">
          <li v-for="c in result.cases" :key="c.id">
            <button
              type="button"
              class="flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-muted/60"
              :class="pr.selectedId.value === c.id ? 'bg-hivis/35' : ''"
              @click="pr.selectCase(c.id)"
            >
              <span class="size-2.5 shrink-0 rounded-full" :class="STATUS_STYLE[c.status].dot" />
              <span class="min-w-0 flex-1">
                <span class="block font-mono text-xs text-muted-foreground">{{ c.id }}</span>
                <span class="block text-sm text-foreground">{{ [c.homes ? `${c.homes} homes` : null, c.storeys ? `${c.storeys} storeys` : null].filter(Boolean).join(' · ') || c.title }} · {{ c.year }}</span>
              </span>
              <span class="shrink-0 text-xs font-semibold" :class="STATUS_STYLE[c.status].text">{{ c.decisionLabel }}</span>
            </button>
          </li>
          <li v-if="!result.cases.length" class="px-3 py-6 text-center text-sm text-muted-foreground">No similar applications found for this council and size.</li>
        </ul>
      </section>

      <!-- Other councils (collapsed) -->
      <section v-if="result.proposal.homes" class="print:hidden">
        <button type="button" class="flex w-full items-center justify-between rounded-md border px-3 py-2.5 text-sm font-medium text-foreground hover:bg-muted/60" :aria-expanded="compareOpen" @click="toggleCompare">
          Compare with the Dublin councils
          <ChevronDown class="size-4 transition-transform" :class="compareOpen ? 'rotate-180' : ''" />
        </button>
        <div v-if="compareOpen" class="mt-2">
          <p v-if="!compareRows" class="text-xs text-muted-foreground">Loading…</p>
          <ul v-else class="divide-y rounded-md border text-sm">
            <li v-for="row in compareRows" :key="row.authority">
              <button
                type="button"
                class="flex w-full items-baseline justify-between gap-3 px-3 py-2 text-left"
                :class="row.authority === result.proposal.authority ? 'bg-hivis/35' : 'hover:bg-muted/60'"
                @click="openCouncil(row.authority)"
              >
                <span class="text-foreground">{{ AUTHORITY_LABEL[row.authority].replace(' County Council', '').replace(' Council', '') }}<span v-if="row.stats" class="text-xs text-muted-foreground"> · {{ row.stats.total }} similar</span></span>
                <span v-if="row.stats?.grantRate != null" class="shrink-0 tabular-nums text-foreground"><strong>{{ percent(row.stats.grantRate) }}</strong> granted<template v-if="row.stats.medianWeeks != null"> · {{ row.stats.medianWeeks }} wks</template></span>
                <span v-else class="shrink-0 text-xs text-muted-foreground">{{ row.stats ? 'Not enough data' : "Couldn't load" }}</span>
              </button>
            </li>
          </ul>
          <p class="mt-1 text-[11px] text-muted-foreground">Same proposal, matched the same way. Click a council to switch.</p>
        </div>
      </section>

      <p v-if="result.proposal.homes && !pr.site.value" class="text-xs text-muted-foreground print:hidden">Tap the map to drop your site and see similar applications within a few km.</p>

      <!-- Sources -->
      <p class="text-[11px] leading-relaxed text-muted-foreground">
        <a :href="result.source.url" target="_blank" rel="noopener" class="underline-offset-2 hover:underline">National Planning Applications register</a>
        · Dept. of Housing · {{ result.source.licence }} · snapshot {{ snapshot }}<template v-if="result.engine === 'predictor'"> · figures from the team planning predictor</template>.
        Past decisions, not a prediction.
      </p>
    </div>
  </div>
</template>
