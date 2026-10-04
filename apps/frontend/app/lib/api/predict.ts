// Client for the planning predictor backend (apps/backend, POST /predict).
// The request and response shapes mirror CONTRACT.md in the repo root.
import type {
  Alternative, Authority, DecisionStatus, DelayFactor, ParsedProposal, PlanningCase, PrecedentsResponse,
} from '~/lib/planning/types'

interface PredictBody {
  description: string
  council: string
  location?: { lat: number, lon: number }
  parsed_override?: { units: number | null, storeys: number | null, mixed_use: boolean }
  max_matches: number
}

interface PredictMatch {
  id: string
  address: string | null
  units: number | null
  storeys: number | null
  decision: string
  received_date: string | null
  decision_date: string | null
  days_to_decision: number | null
  mixed_use: boolean
  further_information: boolean
  appealed: boolean
  lat: number | null
  lon: number | null
  link: string | null
}

interface PredictResponse {
  parsed: { units: number | null, storeys: number | null, mixed_use: boolean, council: string }
  stats: {
    n_similar: number
    grant_rate: number | null
    median_days_to_decision: number | null
    share_further_information: number | null
    share_appealed: number | null
  }
  delay_factors: { factor: DelayFactor['factor'], added_days: number }[]
  site_estimate: { radius_km: number, n_similar: number, median_total_days: number, grant_rate: number } | null
  alternatives: {
    label: string, council: string, lat: number, lon: number, distance_km: number, direction: string
    n_similar: number, median_total_days: number, grant_rate: number, weeks_saved: number, warnings: string[]
  }[]
  summary: string
  matches: PredictMatch[]
  warnings: string[]
}

export interface PredictParams {
  authority: Authority
  /** Plain English. The backend reads it with Claude or rules. */
  description?: string
  /** Skips reading the description: the form values, or a proposal we already parsed. */
  proposal?: ParsedProposal
  /** A dropped pin: adds the site estimate and faster nearby areas. */
  location?: { lat: number, lng: number }
  /** How many closest cases to return (1 to 25). */
  maxMatches?: number
}

const DAYS_PER_WEEK = 7
const REQUEST_TIMEOUT_MS = 30_000

const toWeeks = (days: number) => Math.round(days / DAYS_PER_WEEK)
const toWeeksOrNull = (days: number | null) => (days == null ? null : toWeeks(days))
const round2 = (value: number | null) => (value == null ? null : Math.round(value * 100) / 100)

export class PredictorError extends Error {}

/** One call returns the parsed proposal, stats, summary, cases and, with a pin, the site comparison. */
export async function predict(apiBase: string, params: PredictParams): Promise<PrecedentsResponse> {
  const body: PredictBody = {
    description: params.description ?? '',
    council: params.authority,
    max_matches: params.maxMatches ?? 5,
  }
  if (params.proposal) {
    const { homes, storeys, mixedUse } = params.proposal
    body.parsed_override = { units: homes, storeys, mixed_use: mixedUse }
  }
  if (params.location) body.location = { lat: params.location.lat, lon: params.location.lng }

  let raw: PredictResponse
  try {
    raw = await $fetch<PredictResponse>(`${apiBase.replace(/\/$/, '')}/predict`, {
      method: 'POST', body, timeout: REQUEST_TIMEOUT_MS,
    })
  } catch (cause) {
    throw new PredictorError(describeFailure(cause))
  }
  return toPrecedents(raw, params.authority)
}

function describeFailure(cause: unknown): string {
  const status = (cause as { statusCode?: number, status?: number })?.statusCode ?? (cause as { status?: number })?.status
  if (status === 422) return 'The planning service did not accept that search. Check the description and council.'
  if (status) return 'The planning service had a problem. Try again in a moment.'
  return 'Could not reach the planning service. Check that the API is running.'
}

const STATUS_BY_DECISION: Record<string, DecisionStatus> = { GRANTED: 'granted', REFUSED: 'refused' }
const LABEL_BY_DECISION: Record<string, string> = {
  GRANTED: 'Granted', REFUSED: 'Refused', WITHDRAWN: 'Withdrawn', INVALID: 'Invalid',
}
const DELAY_LABEL: Record<DelayFactor['factor'], string> = {
  further_information_request: 'Further information request',
  appeal: 'Appeal',
}

function toCase(match: PredictMatch, authority: Authority): PlanningCase {
  const { units, storeys } = match
  const title = [units ? `${units} homes` : null, storeys ? `${storeys} storeys` : null].filter(Boolean).join(', ')
  const year = Number(match.received_date?.slice(0, 4)) || null
  return {
    id: match.id,
    authority,
    title: title || 'Housing application',
    location: match.address ?? '',
    coordinates: match.lat != null && match.lon != null ? [match.lon, match.lat] : null,
    year,
    receivedDate: match.received_date,
    decisionDate: match.decision_date,
    homes: units,
    storeys,
    mixedUse: match.mixed_use,
    status: STATUS_BY_DECISION[match.decision] ?? 'closed',
    decisionLabel: LABEL_BY_DECISION[match.decision] ?? match.decision,
    weeks: toWeeksOrNull(match.days_to_decision),
    furtherInfo: match.further_information,
    appealed: match.appealed,
    link: match.link,
  }
}

function toAlternative(alternative: PredictResponse['alternatives'][number]): Alternative {
  return {
    label: alternative.label,
    authority: alternative.council,
    coordinates: [alternative.lon, alternative.lat],
    distanceKm: alternative.distance_km,
    direction: alternative.direction,
    total: alternative.n_similar,
    medianWeeks: toWeeks(alternative.median_total_days),
    grantRate: round2(alternative.grant_rate)!,
    weeksSaved: alternative.weeks_saved,
    warnings: alternative.warnings,
  }
}

function toPrecedents(raw: PredictResponse, authority: Authority): PrecedentsResponse {
  const { stats, site_estimate: site } = raw
  return {
    proposal: { homes: raw.parsed.units, storeys: raw.parsed.storeys, mixedUse: raw.parsed.mixed_use, authority },
    stats: {
      total: stats.n_similar,
      grantRate: round2(stats.grant_rate),
      medianWeeks: toWeeksOrNull(stats.median_days_to_decision),
      furtherInfoShare: round2(stats.share_further_information),
      appealShare: round2(stats.share_appealed),
    },
    cases: raw.matches.map(match => toCase(match, authority)),
    summary: raw.summary,
    delayFactors: raw.delay_factors.map(({ factor, added_days }) => ({
      factor, label: DELAY_LABEL[factor] ?? factor, addedWeeks: toWeeks(added_days),
    })),
    warnings: raw.warnings,
    siteEstimate: site && {
      radiusKm: site.radius_km,
      total: site.n_similar,
      medianWeeks: toWeeks(site.median_total_days),
      grantRate: round2(site.grant_rate)!,
    },
    alternatives: raw.alternatives.map(toAlternative),
  }
}
