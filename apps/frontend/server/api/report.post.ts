import { AUTHORITIES, type Authority, type PlanningCase, type PrecedentsResponse, type ReportResponse, type ReportSection } from '../../app/lib/planning/contract'

interface Profile {
  count: number
  medianHomes: number | null
  medianStoreys: number | null
  mixedUseShare: number | null
  furtherInfoShare: number | null
  medianWeeks: number | null
}

function profile(cases: PlanningCase[]): Profile {
  const storeys = cases.filter(c => c.storeys !== null).map(c => c.storeys!)
  const weeks = cases.filter(c => c.weeks !== null).map(c => c.weeks!)
  return {
    count: cases.length,
    medianHomes: median(cases.filter(c => c.homes !== null).map(c => c.homes!)),
    medianStoreys: median(storeys),
    mixedUseShare: share(cases.filter(c => c.mixedUse).length, cases.length),
    furtherInfoShare: share(cases.filter(c => c.furtherInfo).length, cases.length),
    medianWeeks: median(weeks),
  }
}

const PERIODS = [
  { label: '2018 to 2020', from: 2018, to: 2020 },
  { label: '2021 to 2023', from: 2021, to: 2023 },
  { label: '2024 onwards', from: 2024, to: 9999 },
]

const brief = (c: PlanningCase) => ({ id: c.id, homes: c.homes, storeys: c.storeys, mixedUse: c.mixedUse, year: c.year, weeks: c.weeks, furtherInfo: c.furtherInfo, location: c.location.split(',').slice(-2).join(',').trim() })

/** Every figure the report may use. */
function buildFacts(q: { authority: Authority, homes: number, storeys: number | null, mixedUse: boolean | null }, description: string) {
  const { response, matches } = findPrecedents(q)
  const granted = matches.filter(c => c.status === 'granted')
  const refused = matches.filter(c => c.status === 'refused')
  const byPeriod = PERIODS.map((p) => {
    const inP = matches.filter(c => c.year >= p.from && c.year <= p.to && c.status !== 'pending')
    const g = inP.filter(c => c.status === 'granted').length
    return { period: p.label, decided: inP.length, granted: g, grantRate: inP.length >= 3 ? share(g, inP.length) : null }
  })
  return {
    proposal: { description, authority: q.authority, homes: q.homes, storeys: q.storeys, mixedUse: q.mixedUse },
    since: 2018,
    snapshotDate: response.source.snapshotDate,
    matchRule: response.matchRule,
    widened: response.widened,
    stats: response.stats,
    pending: response.stats.total - response.stats.decided,
    grantedProfile: profile(granted),
    refusedProfile: profile(refused),
    byPeriod,
    closestGranted: granted.slice(0, 3).map(brief),
    closestRefused: refused.slice(0, 3).map(brief),
  }
}
type Facts = ReturnType<typeof buildFacts>

const pct = (v: number | null) => (v === null ? null : `${Math.round(v * 100)}%`)

function templateSections(f: Facts): ReportSection[] {
  const s = f.stats
  const g = f.grantedProfile
  const r = f.refusedProfile
  const cite = (list: { id: string }[]) => list.map(c => c.id)
  const sections: ReportSection[] = []

  sections.push({
    heading: 'Summary',
    paragraphs: [
      `We compared your proposal (${f.proposal.homes} homes${f.proposal.storeys ? `, ${f.proposal.storeys} storeys` : ''}${f.proposal.mixedUse ? ', mixed use' : ''}) with ${s.total} apartment applications made to ${f.proposal.authority} since ${f.since}. Of the ${s.decided} that have been decided, ${s.granted} were granted and ${s.refused} refused${s.grantRate !== null ? ` (${pct(s.grantRate)} granted)` : ''}.`,
      `These are past decisions on applications of a similar size. They are not a prediction for your proposal.${f.widened ? ' There were few close matches, so the size range was widened.' : ''}`,
    ],
    citedIds: [],
  })

  if (g.count && r.count) {
    const lines = [`Granted schemes had a median of ${g.medianHomes} homes${g.medianStoreys !== null ? ` and ${g.medianStoreys} storeys` : ''}; refused schemes had a median of ${r.medianHomes} homes${r.medianStoreys !== null ? ` and ${r.medianStoreys} storeys` : ''}.`]
    if (g.mixedUseShare !== null && r.mixedUseShare !== null) lines.push(`${pct(g.mixedUseShare)} of granted schemes included a non-residential use, against ${pct(r.mixedUseShare)} of refused ones.`)
    if (g.furtherInfoShare !== null && r.furtherInfoShare !== null) lines.push(`The council asked for further information on ${pct(g.furtherInfoShare)} of granted schemes and ${pct(r.furtherInfoShare)} of refused ones.`)
    sections.push({ heading: 'Granted and refused schemes compared', paragraphs: [lines.join(' ')], citedIds: [] })
  }

  const periods = f.byPeriod.filter(p => p.grantRate !== null)
  if (periods.length) {
    sections.push({
      heading: 'Change over time',
      paragraphs: [periods.map(p => `${p.period}: ${p.granted} of ${p.decided} decided applications granted (${pct(p.grantRate)}).`).join(' ')],
      citedIds: [],
    })
  }

  const timing: string[] = []
  if (s.medianWeeks !== null) timing.push(`Decided applications took a median of ${s.medianWeeks} weeks from lodging to decision.`)
  if (s.furtherInfoShare !== null) timing.push(`${pct(s.furtherInfoShare)} received a request for further information.`)
  if (s.furtherInfoExtraWeeks !== null && s.furtherInfoExtraWeeks > 0) timing.push(`Those applications took a median of ${s.furtherInfoExtraWeeks} weeks longer than the rest. This is a comparison between groups, not proof that the request caused the delay.`)
  if (timing.length) sections.push({ heading: 'Timing and further information', paragraphs: [timing.join(' ')], citedIds: [] })

  sections.push({
    heading: 'Appeals',
    paragraphs: [s.appealShare !== null
      ? `${pct(s.appealShare)} of decided applications in this set were appealed to An Bord Pleanála / An Coimisiún Pleanála. The register does not record the grounds of appeal.`
      : 'There were too few decided applications to report on appeals.'],
    citedIds: [],
  })

  const closest = [...f.closestGranted, ...f.closestRefused]
  if (closest.length) {
    const describe = (c: Facts['closestGranted'][number]) => `[${c.id}] ${c.homes} homes${c.storeys ? `, ${c.storeys} storeys` : ''}, ${c.year}`
    sections.push({
      heading: 'Cases worth reading in full',
      paragraphs: [
        f.closestGranted.length ? `Closest granted: ${f.closestGranted.map(describe).join('; ')}.` : '',
        f.closestRefused.length ? `Closest refused: ${f.closestRefused.map(describe).join('; ')}.` : '',
      ].filter(Boolean),
      citedIds: cite(closest),
    })
  }

  sections.push({
    heading: 'What this report cannot tell you',
    paragraphs: [
      'The register does not record why an application was refused, the conditions attached to a grant, or what was said in submissions. Read the planner\'s report on the council file for that.',
      'Matching uses size, height and mixed use only. It does not account for site, zoning, design quality or the current development plan. Treat this as a starting point for a conversation with a planning professional.',
    ],
    citedIds: [],
  })
  return sections
}

/** Report built from the team predictor's figures, so it matches what the screen shows. */
function predictorReport(r: PrecedentsResponse): ReportSection[] {
  const s = r.stats
  const sections: ReportSection[] = [{
    heading: 'Summary',
    paragraphs: [
      r.summary ?? `We found ${s.total} similar applications to ${r.proposal.authority}.`,
      'These are past decisions on applications of a similar size. They are not a prediction for your proposal.',
      ...r.warnings,
    ],
    citedIds: [],
  }]
  const timing: string[] = []
  if (s.medianWeeks !== null) timing.push(`Decided applications took a median of ${s.medianWeeks} weeks from lodging to decision.`)
  if (s.furtherInfoShare !== null) timing.push(`${pct(s.furtherInfoShare)} received a request for further information.`)
  for (const f of r.delayFactors) timing.push(`Applications with ${f.factor === 'appeal' ? 'an appeal' : 'a further information request'} took a median of ${f.addedWeeks} weeks longer in total. This is a comparison between groups, not proof of cause.`)
  if (timing.length) sections.push({ heading: 'Timing and what added time', paragraphs: [timing.join(' ')], citedIds: [] })
  if (s.appealShare !== null) sections.push({ heading: 'Appeals', paragraphs: [`${pct(s.appealShare)} of these applications were appealed. The register does not record the grounds of appeal.`], citedIds: [] })
  if (r.siteEstimate) {
    const lines = [`Within ${r.siteEstimate.radiusKm} km of your site, ${r.siteEstimate.total} similar applications took a median of ${r.siteEstimate.medianWeeks} weeks to a final decision, ${pct(r.siteEstimate.grantRate)} granted.`]
    for (const a of r.alternatives) lines.push(`${a.label} (${a.distanceKm} km ${a.direction}): median ${a.medianWeeks} weeks across ${a.total} applications, about ${a.weeksSaved} weeks faster.`)
    sections.push({ heading: 'Your site and faster nearby areas', paragraphs: lines, citedIds: [] })
  }
  if (r.cases.length) {
    sections.push({
      heading: 'Cases worth reading in full',
      paragraphs: r.cases.map(c => `[${c.id}] ${c.decisionLabel}${c.homes ? `, ${c.homes} homes` : ''}${c.storeys ? `, ${c.storeys} storeys` : ''}${c.decisionDate ? `, decided ${c.decisionDate}` : ''}. ${c.location}`),
      citedIds: r.cases.map(c => c.id),
    })
  }
  sections.push({
    heading: 'What this report cannot tell you',
    paragraphs: ['The register does not record why an application was refused, the conditions attached to a grant, or what was said in submissions. Matching uses size, height and mixed use only, not site, zoning or design. Treat this as a starting point for a conversation with a planning professional.'],
    citedIds: [],
  })
  return sections
}

// POST /api/report { authority, homes, storeys?, mixedUse?, description?, lat?, lon? }
export default defineEventHandler(async (event): Promise<ReportResponse | ReturnType<typeof apiError>> => {
  const body = await readBody<Record<string, unknown>>(event)
  const authority = String(body?.authority ?? '') as Authority
  if (!AUTHORITIES.includes(authority)) return apiError(event, 400, 'VALIDATION', 'authority must be a council name from the national planning register')
  const homes = Number(body?.homes)
  if (!Number.isInteger(homes) || homes < 1) return apiError(event, 400, 'VALIDATION', 'homes must be a positive whole number')
  const storeys = body?.storeys == null || body.storeys === '' ? null : Number(body.storeys)
  if (storeys !== null && (!Number.isInteger(storeys) || storeys < 1)) return apiError(event, 400, 'VALIDATION', 'storeys must be a positive whole number')
  const mixedUse = typeof body?.mixedUse === 'boolean' ? body.mixedUse : null
  const description = typeof body?.description === 'string' ? body.description.slice(0, 600) : ''

  const lat = typeof body?.lat === 'number' ? body.lat : null
  const lon = typeof body?.lon === 'number' ? body.lon : null
  const predicted = await callPredictor({
    description: '',
    council: authority,
    parsed_override: { units: homes, storeys, mixed_use: mixedUse ?? false },
    ...(lat !== null && lon !== null ? { location: { lat, lon } } : {}),
  })
  if (predicted) {
    const r = toPrecedents(predicted, authority, homes, storeys, SOURCE)
    return {
      title: `Planning precedent report: ${homes} homes, ${authority}`,
      sections: predictorReport(r),
      source: 'template',
      generatedAt: new Date().toISOString(),
      basis: `${r.stats.total} similar applications · ${authority} · team predictor`,
    }
  }

  const facts = buildFacts({ authority, homes, storeys, mixedUse }, description)
  const basis = `${facts.stats.total} matched applications · ${authority} · snapshot ${facts.snapshotDate}`
  const fallback: ReportResponse = {
    title: `Planning precedent report: ${homes} homes, ${authority}`,
    sections: templateSections(facts),
    source: 'template',
    generatedAt: new Date().toISOString(),
    basis,
  }
  return fallback
})
