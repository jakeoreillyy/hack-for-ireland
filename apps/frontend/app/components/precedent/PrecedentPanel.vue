<script setup lang="ts">
import ProposalForm from './ProposalForm.vue'
import PrecedentProgress from './PrecedentProgress.vue'
import PrecedentReport from './PrecedentReport.vue'
import CaseCard from './CaseCard.vue'

// Panel routing, RentCheck-style: case card > progress > report > proposal form.
const pr = usePrecedents()
const running = computed(() => ['parsing', 'searching', 'explaining'].includes(pr.state.value))

// Hold the progress view a beat after the last stage ticks, then show the report.
const showReport = useState('pr:show-report', () => false)
const animateReport = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined
watch(() => pr.state.value, (state, prev) => {
  clearTimeout(timer)
  if (state === 'done' && prev && prev !== 'done') {
    timer = setTimeout(() => { animateReport.value = true; showReport.value = true }, 700)
  }
  else if (state !== 'done') showReport.value = false
})
onBeforeUnmount(() => clearTimeout(timer))

const selected = computed(() => (pr.selectedId.value ? pr.caseById(pr.selectedId.value) : undefined))
const view = computed(() => {
  if (selected.value) return `case:${selected.value.id}`
  if (pr.result.value && pr.state.value === 'done' && showReport.value) return 'report'
  if (running.value || pr.state.value === 'done') return 'progress'
  return 'form'
})
</script>

<template>
  <Transition
    mode="out-in"
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0 translate-y-2"
    leave-active-class="transition duration-150 ease-in"
    leave-to-class="opacity-0 -translate-y-1"
  >
    <KeepAlive include="PrecedentReport">
      <CaseCard v-if="selected" :key="view" :item="selected" />
      <PrecedentReport v-else-if="view === 'report'" key="report" :animate="animateReport" />
      <PrecedentProgress v-else-if="view === 'progress'" key="progress" />
      <ProposalForm v-else key="form" />
    </KeepAlive>
  </Transition>
</template>
