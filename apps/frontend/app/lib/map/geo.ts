import type { Feature, FeatureCollection, Geometry, GeoJsonProperties, Polygon } from 'geojson'

export interface LngLat { lng: number; lat: number }

export const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] }

export function featureCollection<G extends Geometry = Geometry, P extends GeoJsonProperties = GeoJsonProperties>(
  features: Feature<G, P>[],
): FeatureCollection<G, P> {
  return { type: 'FeatureCollection', features }
}

/** Circle of `radiusM` metres around `center` as a polygon (no turf dependency). */
export function circlePolygon(center: LngLat, radiusM: number, steps = 64): Feature<Polygon> {
  const R = 6371008.8
  const lat = (center.lat * Math.PI) / 180
  const lng = (center.lng * Math.PI) / 180
  const d = radiusM / R
  const ring: [number, number][] = []
  for (let i = 0; i <= steps; i++) {
    const brng = (i / steps) * 2 * Math.PI
    const lat2 = Math.asin(Math.sin(lat) * Math.cos(d) + Math.cos(lat) * Math.sin(d) * Math.cos(brng))
    const lng2 = lng + Math.atan2(Math.sin(brng) * Math.sin(d) * Math.cos(lat), Math.cos(d) - Math.sin(lat) * Math.sin(lat2))
    ring.push([(lng2 * 180) / Math.PI, (lat2 * 180) / Math.PI])
  }
  return { type: 'Feature', geometry: { type: 'Polygon', coordinates: [ring] }, properties: {} }
}

/** Bounds covering all points, or null if there are none. */
export function boundsOf(points: LngLat[]): [[number, number], [number, number]] | null {
  if (!points.length) return null
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity
  for (const p of points) {
    minLng = Math.min(minLng, p.lng); maxLng = Math.max(maxLng, p.lng)
    minLat = Math.min(minLat, p.lat); maxLat = Math.max(maxLat, p.lat)
  }
  return [[minLng, minLat], [maxLng, maxLat]]
}
