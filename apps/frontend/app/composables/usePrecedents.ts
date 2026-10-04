import { predict, PredictorError } from '~/lib/api/predict'
import type {
  Authority, ParsedProposal, PlanningCase, PrecedentsResponse, PrecedentStats,
} from '~/lib/planning/types'

export type PrecedentState = 'idle' | 'searching' | 'done' | 'error'

/** The cases shown in the list and on the map. */
const MAX_CASES = 20
const SITE_REQUEST_FIELDS = { maxMatches: 1 }

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

export interface SiteState {
  lng: number
  lat: number
  loading: boolean
  estimate: PrecedentsResponse['siteEstimate']
  alternatives: PrecedentsResponse['alternatives']
  warnings: string[]
  error: string | null
}

export function usePrecedents() {
  const apiBase = useRuntimeConfig().public.apiBase
  const call = (params: Parameters<typeof predict>[1]) => predict(apiBase, params)

  // Shared across the shell, map and panels (Nuxt useState).
  const state = useState<PrecedentState>('pr:state', () => 'idle')
  const parsed = useState<ParsedProposal | null>('pr:parsed', () => null)
  const result = useState<PrecedentsResponse | null>('pr:result', () => null)
  const error = useState<string | null>('pr:error', () => null)
  /** The case open in the panel and highlighted on the map. */
  const selectedId = useState<string | null>('pr:selected', () => null)
  /** Bumped to ask the map to fly to the selected case. */
  const focusTick = useState<number>('pr:focus', () => 0)
  /** The description had no number of homes and none was entered: ask before searching. */
  const needsHomes = useState<boolean>('pr:needs-homes', () => false)
  const lastRun = useState<{ description: string, authority: Authority, homes: number | null } | null>('pr:last', () => null)
  const site = useState<SiteState | null>('pr:site', () => null)
  let siteToken = 0

  /**
   * Search in one call: the backend reads the description, finds similar applications and writes
   * the summary. `homes` is used only when the description gives no number of homes.
   */
  async function run(description: string, authority: Authority, homes: number | null = null) {
    lastRun.value = { description, authority, homes }
    needsHomes.value = false
    selectedId.value = null
    result.value = null
    error.value = null
    clearSite()
    state.value = 'searching'
    try {
      let response = await call({ authority, description, maxMatches: MAX_CASES })
      const { proposal } = response
      parsed.value = { homes: proposal.homes, storeys: proposal.storeys, mixedUse: proposal.mixedUse }
      if (!proposal.homes) {
        if (!homes) {
          needsHomes.value = true
          state.value = 'idle'
          return
        }
        response = await call({ authority, proposal: { ...parsed.value, homes }, maxMatches: MAX_CASES })
        parsed.value = { ...parsed.value, homes }
      }
      result.value = response
      state.value = 'done'
    } catch (cause) {
      state.value = 'error'
      error.value = cause instanceof PredictorError ? cause.message : 'Something went wrong. Try again.'
    }
  }

  function retry() {
    if (lastRun.value) return run(lastRun.value.description, lastRun.value.authority, lastRun.value.homes)
  }

  /** The proposal that produced the current results, as the backend takes it. */
  function currentProposal(): ParsedProposal | null {
    const proposal = result.value?.proposal
    return proposal?.homes ? { homes: proposal.homes, storeys: proposal.storeys, mixedUse: proposal.mixedUse } : null
  }

  /** "Drop your site": similar applications within a few km of a point, plus faster nearby areas. */
  async function dropSite(lng: number, lat: number) {
    const current = result.value
    const proposal = currentProposal()
    if (!current || !proposal) return
    const token = ++siteToken
    site.value = { lng, lat, loading: true, estimate: null, alternatives: [], warnings: [], error: null }
    try {
      const response = await call({ authority: current.proposal.authority, proposal, location: { lat, lng }, ...SITE_REQUEST_FIELDS })
      if (token !== siteToken) return
      // Only the caveats this spot adds; the search's own warnings are already shown.
      const warnings = response.warnings.filter(w => !current.warnings.includes(w))
      site.value = {
        lng, lat, loading: false, estimate: response.siteEstimate, alternatives: response.alternatives,
        warnings: response.siteEstimate ? warnings : [],
        // With no estimate the backend's own reason says why, e.g. no applications nearby.
        error: response.siteEstimate ? null : (warnings[0] ?? 'No estimate for this spot.'),
      }
    } catch {
      if (token !== siteToken) return
      site.value = { lng, lat, loading: false, estimate: null, alternatives: [], warnings: [], error: 'The site estimate did not load. Try another spot.' }
    }
  }

  function clearSite() {
    siteToken++
    site.value = null
  }

  /** Headline figures for the same proposal in another council. Null when the request fails. */
  async function compareWith(authority: Authority): Promise<PrecedentStats | null> {
    const proposal = currentProposal()
    if (!proposal) return null
    try {
      return (await call({ authority, proposal, ...SITE_REQUEST_FIELDS })).stats
    } catch {
      return null
    }
  }

  function caseById(id: string): PlanningCase | undefined {
    return result.value?.cases.find(item => item.id === id)
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
    error.value = null
  }

  return {
    state, parsed, result, error, selectedId, focusTick, needsHomes, lastRun, site,
    run, retry, dropSite, clearSite, compareWith, caseById, selectCase, reset,
  }
}
