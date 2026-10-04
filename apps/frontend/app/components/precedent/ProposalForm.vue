<script setup lang="ts">
import { ChevronDown, Search, TriangleAlert } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AUTHORITIES, type Authority } from '~/lib/planning/types'
import { AUTHORITY_LABEL, EXAMPLES } from '~/lib/planning/labels'

const pr = usePrecedents()
const description = useState('pr:form:description', () => pr.lastRun.value?.description ?? '')
const authority = useState<Authority>('pr:form:authority', () => pr.lastRun.value?.authority ?? 'Dublin City Council')
const homes = useState<number | null>('pr:form:homes', () => null)

// Empty number input means "not given", not 0.
const homesInput = computed({
  get: () => homes.value ?? '',
  set: (v: string | number) => { homes.value = v === '' || v == null ? null : Number(v) },
})

function submit() {
  if (!description.value.trim()) return
  pr.run(description.value.trim(), authority.value, homes.value)
}

function useExample(example: typeof EXAMPLES[number]) {
  description.value = example.description
  authority.value = example.authority
  homes.value = null
  submit()
}
</script>

<template>
  <form class="space-y-5 p-5" novalidate @submit.prevent="submit">
    <h1 class="type-display-sm text-balance text-foreground">How did similar housing proposals fare in planning?</h1>

    <div class="space-y-1.5">
      <Label for="pf-description">Describe the development</Label>
      <textarea
        id="pf-description"
        v-model="description"
        rows="3"
        placeholder="For example, 80 apartments in a 6-storey block with ground-floor shops"
        class="w-full resize-y rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
      />
      <div class="flex flex-wrap gap-1.5 pt-1">
        <button
          v-for="example in EXAMPLES"
          :key="example.label"
          type="button"
          class="rounded-md border border-ink/25 bg-background px-2.5 py-1 text-xs font-medium text-foreground transition-colors hover:border-ink hover:bg-hivis/40"
          :title="example.description"
          @click="useExample(example)"
        >
          {{ example.label }}
        </button>
      </div>
    </div>

    <div class="space-y-1.5">
      <Label for="pf-authority">Council</Label>
      <div class="relative">
        <select
          id="pf-authority"
          v-model="authority"
          class="h-10 w-full appearance-none truncate rounded-md border border-input bg-transparent pr-8 pl-3 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
        >
          <option v-for="a in AUTHORITIES" :key="a" :value="a">{{ AUTHORITY_LABEL[a] }}</option>
        </select>
        <ChevronDown class="pointer-events-none absolute top-1/2 right-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
      </div>
    </div>

    <!-- Only when the description gave no number of homes. -->
    <div v-if="pr.needsHomes.value" class="space-y-1.5" role="alert">
      <Label for="pf-homes">How many homes?</Label>
      <Input id="pf-homes" v-model="homesInput" type="number" inputmode="numeric" min="1" max="2000" placeholder="80" class="h-10" />
    </div>

    <div v-if="pr.state.value === 'error'" class="space-y-2 rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm" role="alert">
      <p class="flex items-center gap-1.5 font-semibold text-destructive"><TriangleAlert class="size-4" /> Couldn't load applications</p>
      <p class="text-xs text-muted-foreground">{{ pr.error.value }}</p>
      <Button type="button" size="sm" variant="outline" @click="pr.retry()">Try again</Button>
    </div>

    <Button type="submit" class="h-11 w-full rounded-md btn-hivis bg-hivis text-ink hover:bg-hivis text-[15px]" :disabled="!description.trim()">
      <Search class="size-4" />
      Find similar applications
    </Button>
  </form>
</template>
