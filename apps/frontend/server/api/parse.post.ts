import type { ParsedProposal } from '../../app/lib/planning/contract'

// POST /api/parse { description, authority? }
export default defineEventHandler(async (event): Promise<ParsedProposal | ReturnType<typeof apiError>> => {
  const body = await readBody<{ description?: unknown, authority?: unknown }>(event)
  const description = typeof body?.description === 'string' ? body.description.trim() : ''
  if (description.length < 5) return apiError(event, 400, 'VALIDATION', 'description is required')
  if (description.length > 2000) return apiError(event, 400, 'VALIDATION', 'description must be under 2000 characters')

  // The team predictor reads descriptions with Claude (when it has a key) or its own rules.
  const predicted = await callPredictor({ description, council: typeof body?.authority === 'string' ? body.authority : 'Dublin City Council' })
  if (predicted) return toParsed(predicted)
  return parseByRules(description)
})
