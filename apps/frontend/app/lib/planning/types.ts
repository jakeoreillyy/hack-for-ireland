// View-model types for the UI. The API's own shapes live in `~/lib/api/predict`.

// All 31 councils in the national register, the same names the backend matches on.
// Dublin's four first, the rest A to Z.
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

/** The first four entries of AUTHORITIES. */
export const DUBLIN_AUTHORITIES: readonly Authority[] = AUTHORITIES.slice(0, 4)

/** `closed` = withdrawn or invalid: never decided on the merits, so kept out of rates. */
export type DecisionStatus = 'granted' | 'refused' | 'closed'

export interface ParsedProposal {
  homes: number | null
  storeys: number | null
  mixedUse: boolean
}

export interface PlanningCase {
  id: string                            // the council's application number
  authority: Authority
  title: string                         // e.g. "120 homes, 8 storeys"
  location: string
  coordinates: [number, number] | null  // [lng, lat], WGS84
  year: number | null
  receivedDate: string | null           // ISO date
  decisionDate: string | null           // ISO date
  homes: number | null
  storeys: number | null
  mixedUse: boolean
  status: DecisionStatus
  decisionLabel: string                 // "Granted", "Refused", "Withdrawn", "Invalid"
  weeks: number | null                  // received to decision
  furtherInfo: boolean
  appealed: boolean
  link: string | null                   // null for Dublin City Council and Dún Laoghaire-Rathdown
}

export interface PrecedentStats {
  total: number                         // every similar application, including withdrawn and invalid
  grantRate: number | null              // share of decided (granted or refused) that were granted
  medianWeeks: number | null
  furtherInfoShare: number | null
  appealShare: number | null
}

export interface DelayFactor {
  factor: 'further_information_request' | 'appeal'
  label: string
  addedWeeks: number                    // median extra weeks. A comparison, not a cause.
}

export interface SiteEstimate {
  radiusKm: number
  total: number
  medianWeeks: number                   // received to final decision, including any appeal
  grantRate: number
}

export interface Alternative {
  label: string                         // e.g. "12 km W, South Dublin County Council"
  authority: string
  coordinates: [number, number]         // [lng, lat]
  distanceKm: number
  direction: string                     // compass point from the pin
  total: number
  medianWeeks: number
  grantRate: number
  weeksSaved: number
  warnings: string[]
}

export interface PrecedentsResponse {
  proposal: ParsedProposal & { authority: Authority }
  stats: PrecedentStats
  cases: PlanningCase[]                 // closest first
  summary: string
  delayFactors: DelayFactor[]
  warnings: string[]
  siteEstimate: SiteEstimate | null     // only when a pin was sent
  alternatives: Alternative[]
}
