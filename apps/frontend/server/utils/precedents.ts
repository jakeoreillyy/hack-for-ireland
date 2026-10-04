import type { Authority, PlanningCase, PrecedentStats, PrecedentsResponse } from '../../app/lib/planning/contract'
import snapshot from '../data/precedents.json'

export type SnapshotCase = Omit<PlanningCase, 'match'>
const SNAPSHOT = snapshot as { snapshotDate: string, cases: SnapshotCase[] }
const TOP_N = 25
const MIN_MATCHES = 15

export const SOURCE: PrecedentsResponse['source'] = {
  name: 'Department of Housing, Local Government and Heritage · National Planning Applications',
  url: 'https://data.gov.ie/dataset/planning-application-sites1',
  licence: 'CC BY 4.0',
  snapshotDate: SNAPSHOT.snapshotDate,
}

export interface PrecedentQuery {
  authority: Authority
  homes: number
  storeys: number | null
  mixedUse: boolean | null
}

export function median(values: number[]): number | null {
  if (!values.length) return null
  const s = [...values].sort((a, b) => a - b)
  const mid = Math.floor(s.length / 2)
  return s.length % 2 ? s[mid]! : Math.round((s[mid - 1]! + s[mid]!) / 2)
}

export const share = (part: number, whole: number) => (whole ? Math.round((part / whole) * 100) / 100 : null)

function score(c: SnapshotCase, q: PrecedentQuery): number {
  // Homes closeness: 0 at 4x apart, full marks when equal.
  const homesScore = 1 - Math.min(1, Math.abs(Math.log2((c.homes ?? q.homes) / q.homes)) / 2)
  const storeyScore = q.storeys && c.storeys ? 1 - Math.min(1, Math.abs(c.storeys - q.storeys) / 4) : 0.5
  const mixedScore = q.mixedUse === null ? 0.5 : (c.mixedUse === q.mixedUse ? 1 : 0)
  const recency = Math.min(1, Math.max(0, (c.year - 2018) / 8))
  return Math.round(100 * (0.55 * homesScore + 0.2 * storeyScore + 0.15 * mixedScore + 0.1 * recency))
}

function statsFor(matches: SnapshotCase[], authority: Authority): PrecedentStats {
  const decided = matches.filter(c => c.status !== 'pending')
  const granted = decided.filter(c => c.status === 'granted').length
  const refused = decided.filter(c => c.status === 'refused').length
  const withWeeks = decided.filter(c => c.weeks !== null)
  const withFi = withWeeks.filter(c => c.furtherInfo).map(c => c.weeks!)
  const withoutFi = withWeeks.filter(c => !c.furtherInfo).map(c => c.weeks!)
  const fiMedian = median(withFi)
  const noFiMedian = median(withoutFi)
  return {
    total: matches.length,
    decided: decided.length,
    granted,
    refused,
    grantRate: decided.length >= 3 ? share(granted, granted + refused) : null,
    medianWeeks: median(withWeeks.map(c => c.weeks!)),
    furtherInfoShare: decided.length ? share(decided.filter(c => c.furtherInfo).length, decided.length) : null,
    furtherInfoExtraWeeks: withFi.length >= 3 && withoutFi.length >= 3 && fiMedian !== null && noFiMedian !== null ? fiMedian - noFiMedian : null,
    appealShare: decided.length ? share(decided.filter(c => c.appealed).length, decided.length) : null,
  }
}

/** Matches the proposal against the snapshot. `matches` is every match, best first. */
export function findPrecedents(q: PrecedentQuery): { response: PrecedentsResponse, matches: PlanningCase[] } {
  const inAuthority = SNAPSHOT.cases.filter(c => c.authority === q.authority)
  const within = (lo: number, hi: number, useStoreys: boolean) => inAuthority.filter(c =>
    c.homes !== null && c.homes >= lo && c.homes <= hi
    && (!useStoreys || q.storeys === null || c.storeys === null || Math.abs(c.storeys - q.storeys) <= 2))

  let lo = Math.max(10, Math.floor(q.homes * 0.5))
  let hi = Math.ceil(q.homes * 2)
  let found = within(lo, hi, true)
  let widened = false
  if (found.length < MIN_MATCHES) {
    widened = true
    lo = Math.max(10, Math.floor(q.homes * 0.25))
    hi = Math.ceil(q.homes * 4)
    found = within(lo, hi, false)
  }

  const matches = found
    .map(c => ({ ...c, match: score(c, q) }))
    .sort((a, b) => b.match - a.match || b.year - a.year)

  const rule = [`${q.authority}`, `${lo} to ${hi} homes`]
  if (q.storeys !== null && !widened) rule.push(`${Math.max(1, q.storeys - 2)} to ${q.storeys + 2} storeys where known`)
  rule.push('apartment applications received since 2018')

  return {
    matches,
    response: {
      proposal: { authority: q.authority, homes: q.homes, storeys: q.storeys, mixedUse: q.mixedUse ?? false, kind: 'Apartments', source: 'rules' },
      stats: statsFor(found, q.authority),
      cases: matches.slice(0, TOP_N),
      widened,
      matchRule: rule.join(', '),
      source: SOURCE,
      engine: 'snapshot',
      summary: null,
      delayFactors: [],
      warnings: widened ? ['Few close matches, so size bands were widened.'] : [],
      siteEstimate: null,
      alternatives: [],
    },
  }
}
