import type {
  Authority, ExplainResponse, ParsedProposal, PlanningCase, PrecedentsResponse,
} from '~/lib/planning/contract'

export type PrecedentState = 'idle' | 'parsing' | 'searching' | 'explaining' | 'done' | 'error'

export interface SearchParams {
  authority: Authority
  homes: number
  storeys?: number | null
  mixedUse?: boolean
}

function errorMessage(error: unknown, fallback: string) {
  const data = (error as { data?: { error?: { message?: string } } })?.data
  return data?.error?.message ?? fallback
}

/** Council page for a case: the register link, or (Dublin City) resolved via /api/council-link. */
export async function councilLink(item: PlanningCase): Promise<string | null> {
  if (item.link) return item.link
  if (item.authority !== 'Dublin City Council') return null
  try {
    return (await $fetch<{ url: string }>('/api/council-link', { query: { id: item.id } })).url
  } catch {
    return null
  }
}

export function usePrecedents() {
  // Shared across the shell, map and panels (Nuxt useState), like useMapSelection was for RentCheck.
  const state = useState<PrecedentState>('pr:state', () => 'idle')
  const parsed = useState<ParsedProposal | null>('pr:parsed', () => null)
  const result = useState<PrecedentsResponse | null>('pr:result', () => null)
  const explanation = useState<ExplainResponse | null>('pr:explanation', () => null)
  const error = useState<string | null>('pr:error', () => null)
  /** The case open in the panel and highlighted on the map. */
  const selectedId = useState<string | null>('pr:selected', () => null)
  /** Bumped to ask the map to fly to the selected case. */
  const focusTick = useState<number>('pr:focus', () => 0)

  async function parse(description: string) {
    state.value = 'parsing'
    error.value = null
    try {
      parsed.value = await $fetch<ParsedProposal>('/api/parse', { method: 'POST', body: { description } })
      return parsed.value
    } catch (cause) {
      state.value = 'error'
      error.value = errorMessage(cause, 'Could not read the description. Try again.')
      return null
    }
  }

  async function search(params: SearchParams) {
    state.value = 'searching'
    error.value = null
    explanation.value = null
    try {
      const query: Record<string, string | number | boolean> = { authority: params.authority, homes: params.homes }
      if (params.storeys != null) query.storeys = params.storeys
      if (params.mixedUse != null) query.mixedUse = params.mixedUse
      result.value = await $fetch<PrecedentsResponse>('/api/precedents', { query })
      return result.value
    } catch (cause) {
      state.value = 'error'
      error.value = errorMessage(cause, 'Could not load planning applications from the register.')
      return null
    }
  }

  async function explain(response: PrecedentsResponse) {
    state.value = 'explaining'
    try {
      explanation.value = await $fetch<ExplainResponse>('/api/explain', {
        method: 'POST',
        body: { proposal: response.proposal, stats: response.stats, cases: response.cases },
      })
    } catch {
      // The figures are already on screen; a missing summary is not fatal.
      explanation.value = null
    }
    state.value = 'done'
    return explanation.value
  }

  function caseById(id: string): PlanningCase | undefined {
    return result.value?.cases.find(item => item.id === id)
  }

  /** The description had no number of homes and none was entered: ask before searching. */
  const needsHomes = useState<boolean>('pr:needs-homes', () => false)
  const lastRun = useState<{ description: string; authority: Authority; homes: number | null } | null>('pr:last', () => null)

  /** Parse, search, then explain, in order. `homes` overrides the parsed value. */
  async function run(description: string, authority: Authority, homes: number | null = null) {
    lastRun.value = { description, authority, homes }
    needsHomes.value = false
    selectedId.value = null
    result.value = null
    explanation.value = null
    clearSite()
    const proposal = await parse(description)
    if (!proposal) return
    const count = homes || proposal.homes
    if (!count) {
      needsHomes.value = true
      state.value = 'idle'
      return
    }
    const response = await search({ authority, homes: count, storeys: proposal.storeys, mixedUse: proposal.mixedUse })
    if (!response) return
    await explain(response)
  }

  // "Drop your site": the predictor's estimate within a few km of a point, plus faster nearby areas.
  const site = useState<{ lng: number; lat: number; loading: boolean; estimate: PrecedentsResponse['siteEstimate']; alternatives: PrecedentsResponse['alternatives']; warnings: string[]; error: string | null } | null>('pr:site', () => null)
  let siteToken = 0
  async function dropSite(lng: number, lat: number) {
    const r = result.value
    if (!r?.proposal.homes) return
    const t = ++siteToken
    site.value = { lng, lat, loading: true, estimate: null, alternatives: [], warnings: [], error: null }
    try {
      const query: Record<string, string | number | boolean> = { authority: r.proposal.authority, homes: r.proposal.homes, mixedUse: r.proposal.mixedUse, lat, lon: lng }
      if (r.proposal.storeys) query.storeys = r.proposal.storeys
      const res = await $fetch<PrecedentsResponse>('/api/precedents', { query, timeout: 30000 })
      if (t !== siteToken) return
      // Only the caveats this spot adds; the search's own warnings are already in the report.
      const warnings = (res.warnings ?? []).filter(w => !r.warnings?.includes(w))
      site.value = { lng, lat, loading: false, estimate: res.siteEstimate, alternatives: res.alternatives ?? [], warnings, error: res.siteEstimate ? null : 'No estimate for this spot.' }
    } catch {
      if (t !== siteToken) return
      site.value = { lng, lat, loading: false, estimate: null, alternatives: [], warnings: [], error: 'The site estimate did not load. Try another spot.' }
    }
  }
  function clearSite() {
    siteToken++
    site.value = null
  }

  function retry() {
    if (lastRun.value) return run(lastRun.value.description, lastRun.value.authority, lastRun.value.homes)
  }

  function selectCase(id: string | null, focus = true) {
    selectedId.value = id
    if (id && focus) focusTick.value++
  }

  function reset() {
    clearSite()
    needsHomes.value = false
    selectedId.value = null
    state.value = 'idle'
    parsed.value = null
    result.value = null
    explanation.value = null
    error.value = null
  }

  return { state, parsed, result, explanation, error, selectedId, focusTick, needsHomes, lastRun, run, retry, site, dropSite, clearSite, parse, search, explain, caseById, selectCase, reset }
}
