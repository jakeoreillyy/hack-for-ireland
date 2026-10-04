import type { ExplainResponse, PrecedentsResponse } from '../../app/lib/planning/contract'

/** Deterministic summary built only from the computed stats. */
function template(res: Pick<PrecedentsResponse, 'proposal' | 'stats' | 'cases'> & { engine?: PrecedentsResponse['engine'] }): ExplainResponse {
  const { stats, proposal } = res
  // The snapshot covers 2018 onwards; the predictor covers the whole register.
  const since = res.engine === 'predictor' ? '' : ' since 2018'
  const parts = [stats.granted !== null && stats.refused !== null
    ? `Of ${stats.total} similar applications to ${proposal.authority}${since}, ${stats.granted} were granted and ${stats.refused} refused.`
    : `We found ${stats.total} similar applications to ${proposal.authority}${since}.`]
  if (stats.medianWeeks !== null) parts.push(`Decided cases typically took ${stats.medianWeeks} weeks.`)
  const extra = stats.furtherInfoExtraWeeks
  if (extra !== null && extra !== 0) {
    parts.push(`Those with a further information request took a median of ${Math.abs(extra)} weeks ${extra > 0 ? 'longer' : 'less'} than those without.`)
  }
  const cited = res.cases.slice(0, 3).map(c => c.id)
  if (cited.length) parts.push(`Closest matches: ${cited.map(id => `[${id}]`).join(', ')}.`)
  return { text: parts.join(' '), citedIds: cited, source: 'template' }
}

// POST /api/explain { proposal, stats, cases } (as returned by /api/precedents)
export default defineEventHandler(async (event): Promise<ExplainResponse | ReturnType<typeof apiError>> => {
  const body = await readBody<Partial<PrecedentsResponse>>(event)
  if (!body?.stats || !Array.isArray(body.cases) || !body.proposal?.authority) {
    return apiError(event, 400, 'VALIDATION', 'send { proposal, stats, cases } as returned by /api/precedents')
  }
  // On the predictor engine, use the team predictor's own summary so the wording matches its figures.
  if (body.engine === 'predictor' && body.summary) {
    return { text: body.summary, citedIds: [], source: 'template' }
  }
  return template(body as PrecedentsResponse)
})
