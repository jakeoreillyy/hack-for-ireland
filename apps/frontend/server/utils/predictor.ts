// Client for the team's planning predictor (hack-for-ireland apps/backend, POST /predict).
// Enabled when NUXT_PREDICTOR_URL is set. Every caller falls back to the local snapshot
// when it is unset, down or slow, so the demo never depends on a second process.
import type { Authority, DelayFactor, ParsedProposal, PlanningCase, PrecedentsResponse } from '../../app/lib/planning/contract'
import predictorData from '../data/predictor-cases.json'
import snapshot from '../data/precedents.json'

interface PredictResponse {
  parsed: { units: number | null, storeys: number | null, mixed_use: boolean, council: string }
  stats: { n_similar: number, grant_rate: number | null, median_days_to_decision: number | null, share_further_information: number | null, share_appealed: number | null }
  delay_factors: { factor: DelayFactor['factor'], added_days: number }[]
  site_estimate: { radius_km: number, n_similar: number, median_total_days: number, grant_rate: number } | null
  alternatives: { label: string, council: string, lat: number, lon: number, distance_km: number, direction: string, n_similar: number, median_total_days: number, grant_rate: number, weeks_saved: number, warnings: string[] }[]
  summary: string
  matches: { id: string, address: string | null, units: number | null, storeys: number | null, decision: string, decision_date: string | null, link: string | null }[]
  warnings: string[]
}

interface PredictorCase {
  id: string, authority: string, location: string, coordinates: [number, number]
  receivedDate: string | null, decisionDate: string | null, homes: number | null, storeys: number | null
  mixedUse: boolean, decision: string, daysToDecision: number | null, furtherInfo: boolean, appealed: boolean, link: string | null
}
const DETAILS = (predictorData as { cases: Record<string, PredictorCase> }).cases
const DESCRIPTIONS = new Map((snapshot as { cases: PlanningCase[] }).cases.map(c => [`${c.authority}|${c.id}`, c]))

const weeks = (days: number | null | undefined) => (days == null ? null : Math.round(days / 7))
const round2 = (v: number | null) => (v == null ? null : Math.round(v * 100) / 100)
const FACTOR_LABEL: Record<DelayFactor['factor'], string> = {
  further_information_request: 'Further information request',
  appeal: 'Appeal',
}

export function predictorEnabled(): boolean {
  return !!useRuntimeConfig().predictorUrl
}

export async function callPredictor(body: Record<string, unknown>): Promise<PredictResponse | null> {
  const base = useRuntimeConfig().predictorUrl as string
  if (!base) return null
  try {
    return await $fetch<PredictResponse>(`${base.replace(/\/$/, '')}/predict`, { method: 'POST', body, timeout: 15000 })
  }
  catch (err) {
    console.warn('[predictor] /predict failed, using local snapshot:', (err as Error).message)
    return null
  }
}

export function toParsed(p: PredictResponse): ParsedProposal {
  return { homes: p.parsed.units, storeys: p.parsed.storeys, mixedUse: p.parsed.mixed_use, kind: 'Apartments', source: 'rules' }
}

function toCase(m: PredictResponse['matches'][number], authority: Authority, rank: number): PlanningCase | null {
  const d = DETAILS[`${authority}|${m.id}`]
  if (!d) return null
  const ours = DESCRIPTIONS.get(`${authority}|${m.id}`)
  const decision = m.decision.toLowerCase()
  const status = decision === 'granted' ? 'granted' : decision === 'refused' ? 'refused' : 'pending'
  const homes = m.units ?? d.homes
  const storeys = m.storeys ?? d.storeys
  const year = d.receivedDate ? Number(d.receivedDate.slice(0, 4)) : Number((m.decision_date ?? '').slice(0, 4)) || 0
  return {
    id: m.id,
    authority,
    title: ours?.title ?? [homes ? `${homes} homes` : 'Housing', storeys ? `${storeys} storeys` : null, d.mixedUse ? 'mixed use' : null].filter(Boolean).join(', '),
    description: ours?.description ?? '',
    location: m.address ?? d.location,
    coordinates: d.coordinates,
    year,
    receivedDate: d.receivedDate ?? '',
    decisionDate: m.decision_date ?? d.decisionDate,
    homes,
    storeys,
    mixedUse: d.mixedUse,
    status,
    // /predict also returns withdrawn and invalid applications; label them as such, not as pending.
    decisionLabel: status === 'granted' ? 'Granted' : status === 'refused' ? 'Refused' : decision ? decision.charAt(0).toUpperCase() + decision.slice(1) : 'Awaiting decision',
    weeks: weeks(d.daysToDecision),
    furtherInfo: d.furtherInfo,
    appealed: d.appealed,
    link: m.link ?? d.link,
    match: Math.max(50, 100 - rank * 5), // /predict returns closest first; it has no score of its own
  }
}

const ALL_DETAILS = Object.values(DETAILS)

/** A readable place name for a point: the locality of the nearest application in that council. */
function placeNear(lon: number, lat: number, council: string): string {
  let best: PredictorCase | null = null
  let bestD = Infinity
  for (const c of ALL_DETAILS) {
    if (c.authority !== council) continue
    const d = (c.coordinates[0] - lon) ** 2 + (c.coordinates[1] - lat) ** 2
    if (d < bestD) { bestD = d; best = c }
  }
  // Addresses end "..., Clondalkin, Dublin 22": take the first part that isn't a number, eircode or "Co. X".
  const parts = (best?.location ?? '').split(',').map(p => p.trim().replace(/\.$/, '').replace(/\s+(co\.?|county)\s+\w+$/i, '')).filter(Boolean).reverse()
  const place = parts.find(p => !/\d|^co\.?\s|^county\s|^ireland$/i.test(p))
  return place ?? council
}

/** Maps a /predict response onto our contract. */
export function toPrecedents(p: PredictResponse, authority: Authority, homes: number, storeys: number | null, source: PrecedentsResponse['source']): PrecedentsResponse {
  const s = p.stats
  const fi = p.delay_factors.find(f => f.factor === 'further_information_request')
  return {
    proposal: { authority, homes, storeys, mixedUse: p.parsed.mixed_use, kind: 'Apartments', source: 'rules' },
    stats: {
      total: s.n_similar,
      decided: null,
      granted: null,
      refused: null,
      grantRate: round2(s.grant_rate),
      medianWeeks: weeks(s.median_days_to_decision),
      furtherInfoShare: round2(s.share_further_information),
      furtherInfoExtraWeeks: fi ? weeks(fi.added_days) : null,
      appealShare: round2(s.share_appealed),
    },
    cases: p.matches.map((m, i) => toCase(m, authority, i)).filter((c): c is PlanningCase => !!c),
    widened: p.warnings.some(w => /widened/i.test(w)),
    matchRule: `${authority}, closest in size to ${homes} homes${storeys ? ` and ${storeys} storeys` : ''}, all apartment applications in the register (team predictor)`,
    source,
    engine: 'predictor',
    summary: p.summary,
    delayFactors: p.delay_factors.map(f => ({ factor: f.factor, label: FACTOR_LABEL[f.factor] ?? f.factor, addedWeeks: weeks(f.added_days)! })),
    warnings: p.warnings,
    siteEstimate: p.site_estimate && {
      radiusKm: p.site_estimate.radius_km,
      total: p.site_estimate.n_similar,
      medianWeeks: weeks(p.site_estimate.median_total_days)!,
      grantRate: round2(p.site_estimate.grant_rate)!,
    },
    alternatives: p.alternatives.map(a => ({
      label: `Near ${placeNear(a.lon, a.lat, a.council)}`, authority: a.council, coordinates: [a.lon, a.lat] as [number, number], distanceKm: a.distance_km,
      direction: a.direction, total: a.n_similar, medianWeeks: weeks(a.median_total_days)!, grantRate: round2(a.grant_rate)!,
      weeksSaved: a.weeks_saved, warnings: a.warnings,
    })),
  }
}
