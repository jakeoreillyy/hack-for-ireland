import { AUTHORITIES, SNAPSHOT_AUTHORITIES, type Authority, type PrecedentsResponse } from '../../app/lib/planning/contract'

// GET /api/precedents?authority=&homes=&storeys=&mixedUse=&lat=&lon=
export default defineEventHandler(async (event): Promise<PrecedentsResponse | ReturnType<typeof apiError>> => {
  const q = getQuery(event)
  const authority = String(q.authority ?? '') as Authority
  if (!AUTHORITIES.includes(authority)) return apiError(event, 400, 'VALIDATION', 'authority must be a council name from the national planning register')
  const homes = Number(q.homes)
  if (!Number.isInteger(homes) || homes < 1) return apiError(event, 400, 'VALIDATION', 'homes must be a positive whole number')
  const storeys = q.storeys != null && q.storeys !== '' ? Number(q.storeys) : null
  if (storeys !== null && (!Number.isInteger(storeys) || storeys < 1)) return apiError(event, 400, 'VALIDATION', 'storeys must be a positive whole number')
  const mixedUse = q.mixedUse === 'true' ? true : q.mixedUse === 'false' ? false : null

  const lat = q.lat != null && q.lat !== '' ? Number(q.lat) : null
  const lon = q.lon != null && q.lon !== '' ? Number(q.lon) : null
  const location = lat !== null && lon !== null && Number.isFinite(lat) && Number.isFinite(lon) ? { lat, lon } : null

  const snapshotResult = findPrecedents({ authority, homes, storeys, mixedUse }).response
  const predicted = await callPredictor({
    description: '',
    council: authority,
    parsed_override: { units: homes, storeys, mixed_use: mixedUse ?? false },
    ...(location ? { location } : {}),
  })
  if (predicted) return toPrecedents(predicted, authority, homes, storeys, snapshotResult.source)
  if (!SNAPSHOT_AUTHORITIES.includes(authority)) {
    snapshotResult.warnings.push(`The planning predictor is offline and the local copy only covers the four Dublin councils, so there are no results for ${authority} right now.`)
  }
  else if (predictorEnabled()) snapshotResult.warnings.push('Team predictor unavailable, so these figures come from the local Dublin snapshot.')
  return snapshotResult
})
