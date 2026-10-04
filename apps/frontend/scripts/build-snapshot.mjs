// Pulls apartment applications for the four Dublin councils from the national
// planning register and writes server/data/precedents.json.
// Run from frontend/: node scripts/build-snapshot.mjs
import { writeFile, mkdir } from 'node:fs/promises'
import { extractHomes, extractStoreys, isMixedUse, extractKind, stripApplicant, titleFor } from '../server/utils/rules.ts'

const API = 'https://services.arcgis.com/NzlPQPKn5QF9v2US/arcgis/rest/services/IrishPlanningApplications/FeatureServer/0/query'
const AUTHORITIES = [
  'Dublin City Council',
  'South Dublin County Council',
  'Fingal County Council',
  'Dun Laoghaire Rathdown County Council',
]
// Never request Applicant* fields.
const FIELDS = [
  'ApplicationNumber', 'PlanningAuthority', 'DevelopmentDescription', 'DevelopmentAddress',
  'NumResidentialUnits', 'Decision', 'ReceivedDate', 'DecisionDate', 'FIRequestDate',
  'AppealStatus', 'AppealDecision', 'AppealRefNumber', 'AppealSubmittedDate', 'LinkAppDetails',
].join(',')
const PAGE = 2000
const WEEK_MS = 7 * 24 * 3600 * 1000

async function fetchAuthority(authority) {
  const rows = []
  for (let offset = 0; ; offset += PAGE) {
    const params = new URLSearchParams({
      where: `PlanningAuthority='${authority}' AND DevelopmentDescription LIKE '%apartment%' AND ReceivedDate >= DATE '2018-01-01'`,
      outFields: FIELDS,
      outSR: '4326',
      resultOffset: String(offset),
      resultRecordCount: String(PAGE),
      orderByFields: 'OBJECTID',
      f: 'json',
    })
    const res = await fetch(`${API}?${params}`)
    if (!res.ok) throw new Error(`${authority}: HTTP ${res.status}`)
    const body = await res.json()
    if (body.error) throw new Error(`${authority}: ${body.error.message}`)
    rows.push(...body.features)
    if (!body.exceededTransferLimit && body.features.length < PAGE) break
  }
  return rows
}

function normaliseDecision(raw) {
  const d = (raw ?? '').trim().toUpperCase()
  if (d.includes('INVALID') || d.endsWith('INVA') || d.includes('WITHDRAW')) return null
  if (d.startsWith('SPLIT')) return { status: 'granted', decisionLabel: 'Split decision' }
  if (d.includes('GRANT')) return { status: 'granted', decisionLabel: 'Granted' }
  if (d.includes('REFUSE')) return { status: 'refused', decisionLabel: 'Refused' }
  if (d === '' || d.includes('ADDITIONAL INFORMATION')) return { status: 'pending', decisionLabel: 'Awaiting decision' }
  return null
}

const isoDate = ms => (ms ? new Date(ms).toISOString().slice(0, 10) : null)

function toCase(feature) {
  const a = feature.attributes
  const g = feature.geometry
  if (!g || !Number.isFinite(g.x) || !Number.isFinite(g.y) || !a.ReceivedDate) return null
  const id = (a.ApplicationNumber ?? '').trim()
  // Extensions of duration (/E, /FEP, trailing E) re-approve an old permission; not a fresh decision.
  if (!id || /(\/E|\/EP|\/FEP|\/EXT|\dE)$/i.test(id)) return null
  const decision = normaliseDecision(a.Decision)
  if (!decision) return null

  const text = a.DevelopmentDescription ?? ''
  let homes = extractHomes(text)
  // NumResidentialUnits is unreliable for Dublin City Council; only trust it elsewhere.
  if (homes === null && a.PlanningAuthority !== 'Dublin City Council' && a.NumResidentialUnits > 0) homes = a.NumResidentialUnits
  if (homes === null || homes < 10) return null

  const storeys = extractStoreys(text)
  const mixedUse = isMixedUse(text)
  const kind = extractKind(text)
  const weeks = decision.status !== 'pending' && a.DecisionDate
    ? Math.max(0, Math.round((a.DecisionDate - a.ReceivedDate) / WEEK_MS))
    : null

  return {
    id,
    authority: a.PlanningAuthority,
    title: titleFor({ homes, storeys, mixedUse, kind }),
    description: stripApplicant(text),
    location: (a.DevelopmentAddress ?? '').trim(),
    coordinates: [Number(g.x.toFixed(6)), Number(g.y.toFixed(6))],
    year: new Date(a.ReceivedDate).getUTCFullYear(),
    receivedDate: isoDate(a.ReceivedDate),
    decisionDate: decision.status === 'pending' ? null : isoDate(a.DecisionDate),
    homes,
    storeys,
    mixedUse,
    status: decision.status,
    decisionLabel: decision.decisionLabel,
    weeks,
    furtherInfo: a.FIRequestDate != null,
    // Dublin City leaves AppealStatus empty but fills AppealRefNumber / AppealSubmittedDate.
    appealed: a.AppealSubmittedDate != null || !!(a.AppealRefNumber ?? '').trim() || !!(a.AppealStatus ?? '').trim(),
    link: a.LinkAppDetails || null,
  }
}

const cases = []
for (const authority of AUTHORITIES) {
  const rows = await fetchAuthority(authority)
  const kept = rows.map(toCase).filter(Boolean)
  const byStatus = kept.reduce((acc, c) => ({ ...acc, [c.status]: (acc[c.status] ?? 0) + 1 }), {})
  console.log(`${authority}: ${rows.length} fetched, ${kept.length} kept`, byStatus)
  cases.push(...kept)
}

// One record per application number (amendments can repeat).
const unique = [...new Map(cases.map(c => [`${c.authority}|${c.id}`, c])).values()]
const snapshotDate = new Date().toISOString().slice(0, 10)
await mkdir(new URL('../server/data/', import.meta.url), { recursive: true })
await writeFile(new URL('../server/data/precedents.json', import.meta.url), JSON.stringify({ snapshotDate, cases: unique }))
console.log(`Wrote ${unique.length} cases, snapshot ${snapshotDate}`)
