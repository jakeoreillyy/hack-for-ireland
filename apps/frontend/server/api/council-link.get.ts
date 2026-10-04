// GET /api/council-link?id=WEB2412/25 → { url }
// The register has no LinkAppDetails for Dublin City Council, but its cases live on the same
// Agile planning portal as South Dublin's. Resolve the application number to the portal's
// internal id so the UI can open the real case page. Owned by Agent 2.
const PORTAL = 'https://planning.agileapplications.ie/dublincity/application-details/'
const SEARCH = 'https://planningapi.agileapplications.ie/api/application/search'
const ID_PATTERN = /^[A-Z0-9][A-Z0-9/-]{2,30}$/i

const cache = new Map<string, string | null>()

export default defineEventHandler(async (event) => {
  const id = String(getQuery(event).id ?? '').trim()
  if (!ID_PATTERN.test(id)) return apiError(event, 400, 'BAD_ID', 'Give an application number, e.g. WEB2412/25.')

  if (!cache.has(id)) {
    try {
      const res = await $fetch<{ results?: { id: number, reference: string }[] }>(SEARCH, {
        query: { reference: id },
        headers: { 'x-client': 'DCC', 'x-product': 'CITIZENPORTAL', 'x-service': 'PA' },
        timeout: 6000,
      })
      // Only the portal id is read; the response's applicant fields are ignored.
      const hit = res.results?.find(r => r.reference.toUpperCase() === id.toUpperCase())
      cache.set(id, hit ? `${PORTAL}${hit.id}` : null)
    } catch {
      return apiError(event, 502, 'PORTAL_UNAVAILABLE', 'The council planning portal did not respond.')
    }
  }

  const url = cache.get(id)
  if (!url) return apiError(event, 404, 'NOT_FOUND', 'This application number was not found on the council portal.')
  return { url }
})
