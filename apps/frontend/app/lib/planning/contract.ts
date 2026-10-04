// Shared between server/ and app/. Owned by Agent 1. Additive changes only.

// All 31 councils in the national register (team predictor data). Dublin's four first,
// the rest A to Z. The local snapshot fallback covers only the Dublin four.
export const AUTHORITIES = [
  'Dublin City Council',
  'South Dublin County Council',
  'Fingal County Council',
  'Dun Laoghaire Rathdown County Council',
  'Carlow County Council',
  'Cavan County Council',
  'Clare County Council',
  'Cork City Council',
  'Cork County Council',
  'Donegal County Council',
  'Galway City Council',
  'Galway County Council',
  'Kerry County Council',
  'Kildare County Council',
  'Kilkenny County Council',
  'Laois County Council',
  'Leitrim County Council',
  'Limerick County Council',
  'Longford County Council',
  'Louth County Council',
  'Mayo County Council',
  'Meath County Council',
  'Monaghan County Council',
  'Offaly County Council',
  'Roscommon County Council',
  'Sligo County Council',
  'Tipperary County Council',
  'Waterford City and County Council',
  'Westmeath County Council',
  'Wexford County Council',
  'Wicklow County Council',
] as const

export type Authority = typeof AUTHORITIES[number]

/** Councils the local snapshot covers; others need the team predictor running. */
export const SNAPSHOT_AUTHORITIES: readonly Authority[] = AUTHORITIES.slice(0, 4)

/** Council decision. Appeals are tracked separately in `appealed`. */
export type DecisionStatus = 'granted' | 'refused' | 'pending'

export interface ParsedProposal {
  homes: number | null
  storeys: number | null
  mixedUse: boolean
  kind: string            // e.g. "Apartments", "Build-to-rent", "Student accommodation"
  source: 'ai' | 'rules'  // 'rules' = regex fallback, no model was called
}

export interface PlanningCase {
  id: string                    // ApplicationNumber, e.g. "SD23A/0123"
  authority: Authority
  title: string                 // short, human title (no applicant names)
  description: string           // DevelopmentDescription, applicant name prefix stripped
  location: string              // DevelopmentAddress
  coordinates: [number, number] // [lng, lat], WGS84
  year: number                  // from ReceivedDate
  receivedDate: string          // ISO date
  decisionDate: string | null   // ISO date
  homes: number | null
  storeys: number | null
  mixedUse: boolean
  status: DecisionStatus
  decisionLabel: string         // human label, e.g. "Granted", "Refused", "Split decision", "Awaiting decision"
  weeks: number | null          // received to decision, rounded
  furtherInfo: boolean          // FIRequestDate present
  appealed: boolean | null      // from AppealSubmittedDate / AppealRefNumber (all four councils publish these)
  link: string | null           // LinkAppDetails; null for Dublin City Council
  match: number                 // 0-100 similarity to the proposal
}

export interface PrecedentStats {
  total: number                 // all matched applications, not just the returned `cases`
  // null when engine === 'predictor': /predict returns only the rate, not the counts.
  decided: number | null
  granted: number | null
  refused: number | null
  grantRate: number | null      // granted / (granted + refused), null if decided < 3
  medianWeeks: number | null
  furtherInfoShare: number | null
  /** Median weeks WITH a further info request minus WITHOUT. A comparison, not a cause. */
  furtherInfoExtraWeeks: number | null
  appealShare: number | null    // null when there are no decided cases
}

export interface PrecedentsResponse {
  proposal: ParsedProposal & { authority: Authority }
  stats: PrecedentStats
  cases: PlanningCase[]         // top 25 by match, best first
  widened: boolean              // true if the match bands had to be widened
  matchRule: string             // plain English, e.g. "Same council, 60 to 240 homes, since 2018"
  source: {
    name: string                // "Department of Housing, Local Government and Heritage · National Planning Applications"
    url: string                 // "https://data.gov.ie/dataset/planning-application-sites1"
    licence: 'CC BY 4.0'
    snapshotDate: string        // ISO date the snapshot was pulled
  }
  // ── Added 14:50: the predictor backend (hack-for-ireland apps/backend, POST /predict) ──
  /** 'predictor' = figures from the team's FastAPI backend; 'snapshot' = local fallback. */
  engine: 'predictor' | 'snapshot'
  /** Plain-English summary from the predictor, or null on the snapshot engine. */
  summary: string | null
  /** Median extra weeks seen with each factor. Comparisons, not causes. */
  delayFactors: DelayFactor[]
  /** Short caveats to show as-is, e.g. "Few close matches, so size bands were widened." */
  warnings: string[]
  /** Only when the request included lat/lon (a dropped pin). */
  siteEstimate: SiteEstimate | null
  alternatives: Alternative[]
}

export interface DelayFactor {
  factor: 'further_information_request' | 'appeal'
  label: string                 // "Further information request", "Appeal"
  addedWeeks: number
}

export interface SiteEstimate {
  radiusKm: number
  total: number
  medianWeeks: number           // received to final decision, including any appeal
  grantRate: number
}

export interface Alternative {
  label: string                 // e.g. "Near Clondalkin, South Dublin"
  authority: string
  coordinates: [number, number] // [lng, lat]
  distanceKm: number
  direction: string             // compass point from the pin
  total: number
  medianWeeks: number
  grantRate: number
  weeksSaved: number
  warnings: string[]
}

export interface ExplainResponse {
  text: string
  citedIds: string[]            // every id here exists in the cases sent
  source: 'ai' | 'template'
}

// ── Added 14:45 for the written report (POST /api/report) ──

export interface ReportSection {
  heading: string
  paragraphs: string[]
  citedIds: string[]            // every id exists in the matched cases
}

export interface ReportResponse {
  title: string
  sections: ReportSection[]     // 5 to 7 sections, in reading order
  source: 'ai' | 'template'
  generatedAt: string           // ISO timestamp
  basis: string                 // e.g. "43 matched applications · Dublin City Council · snapshot 2026-10-04"
}
