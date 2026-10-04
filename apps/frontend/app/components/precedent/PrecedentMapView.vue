<script setup lang="ts">
import 'maplibre-gl/dist/maplibre-gl.css'
import '~/lib/map/map.css'
import { Marker, type Map as MlMap, type MapMouseEvent } from 'maplibre-gl'
import { useMediaQuery } from '@vueuse/core'
import { Copy, ExternalLink, FileText, PersonStanding } from '@lucide/vue'
import { toast } from 'vue-sonner'
import RadialMenu, { type RadialItem } from '~/components/map/RadialMenu.vue'
import { CAMERA, DESKTOP_QUERY, DUBLIN_CENTER, PITCH_3D } from '~/lib/map/config'
import { createMap, ensureLayer, ensureSource, firstSymbolLayer, softenBuildings } from '~/lib/map/core'
import { token } from '~/lib/map/colors'
import { circlePolygon } from '~/lib/map/geo'
import { clearBuildingHighlight, highlightBuildingWhenSettled, removeBuildingHighlight } from '~/lib/map/building'
import { fitPoints, flyToProperty, startOrbit } from '~/lib/map/camera'
import { CasePins } from '~/lib/map/casePins'
import { useMapUi } from '~/lib/map/state'
import type { PlanningCase } from '~/lib/planning/types'

const container = ref<HTMLDivElement>()
const map = shallowRef<MlMap | null>(null)
const ui = useMapUi()
const pr = usePrecedents()
const hovered = useState<string | null>('pr:hover', () => null)
const desktop = useMediaQuery(DESKTOP_QUERY)
const flat = computed(() => !(ui.is3D.value ?? desktop.value))
const cases = computed(() => pr.result.value?.cases ?? [])

let pins: CasePins | null = null
let stopOrbit: (() => void) | null = null

type LocatedCase = PlanningCase & { coordinates: [number, number] }
const lngLat = (c: LocatedCase) => ({ lng: c.coordinates[0], lat: c.coordinates[1] })
// Ignore cases without a point, or outside Ireland, so one bad coordinate can't zoom the camera out to sea.
const inIreland = (c: PlanningCase): c is LocatedCase => c.coordinates !== null && c.coordinates[0] > -11 && c.coordinates[0] < -5 && c.coordinates[1] > 51 && c.coordinates[1] < 56

onMounted(async () => {
  const start = flat.value ? CAMERA.mobileBrowse : CAMERA.browse
  const { map: m, ready } = createMap({ container: container.value!, center: DUBLIN_CENTER, ...start, zoom: 11.5 })
  m.dragRotate.enable()
  m.touchZoomRotate.enableRotation()
  const { fallback } = await ready
  if (fallback) toast('Using simplified map')
  if (!m.loaded()) await new Promise(r => m.once('load', r))

  softenBuildings(m)
  addColumns(m)
  pins = new CasePins(m, {
    hover: id => (hovered.value = id),
    select: (id) => {
      // Tap the selected pin again for its actions.
      const c = pr.caseById(id)
      if (id === pr.selectedId.value && c?.coordinates) openRadialOnPin(id, m.project(c.coordinates))
      else pr.selectCase(id)
    },
    context: openRadialOnPin,
  })
  m.on('contextmenu', (e: MapMouseEvent) => openRadial(e.point, e.lngLat))
  m.on('movestart', closeRadial)
  m.on('click', onMapClick)
  map.value = m
  syncCases()
})

onBeforeUnmount(() => {
  siteMarker?.remove()
  stopOrbit?.()
  pins?.destroy()
  removeBuildingHighlight(map.value)
  map.value?.remove()
  map.value = null
})

// --- proposed-height columns ---------------------------------------------------
// Each matched case stands on its site as a translucent column, storeys × 3 m tall
// (the register's storey count), coloured by the council's decision.
const COLUMNS = 'precedent-columns'
const STOREY_M = 3

function columnData(): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: cases.value.filter(inIreland).map((c) => {
      const f = circlePolygon(lngLat(c), 22, 32)
      return { ...f, id: c.id, properties: { id: c.id, status: c.status, height: c.storeys ? c.storeys * STOREY_M : 2 } }
    }),
  }
}

function addColumns(m: MlMap) {
  ensureSource(m, COLUMNS, { type: 'geojson', data: columnData(), promoteId: 'id' })
  ensureLayer(m, {
    id: COLUMNS,
    type: 'fill-extrusion',
    source: COLUMNS,
    paint: {
      'fill-extrusion-color': [
        'case', ['boolean', ['feature-state', 'selected'], false], token('--hivis', '#ffd400'),
        ['match', ['get', 'status'],
          'granted', token('--planning-granted', '#1f7a44'),
          'refused', token('--planning-refused', '#b42318'),
          token('--planning-closed', '#6b7280')],
      ],
      'fill-extrusion-height': ['get', 'height'],
      'fill-extrusion-base': 0,
      'fill-extrusion-opacity': 0.72,
    },
  }, firstSymbolLayer(m))
}

let selectedColumn: string | null = null
function syncColumns() {
  const m = map.value
  const src = m?.getSource(COLUMNS) as { setData?: (d: unknown) => void } | undefined
  src?.setData?.(columnData())
  selectColumn()
}
function selectColumn() {
  const m = map.value
  if (!m?.getSource(COLUMNS)) return
  if (selectedColumn) m.setFeatureState({ source: COLUMNS, id: selectedColumn }, { selected: false })
  selectedColumn = pr.selectedId.value
  if (selectedColumn) m.setFeatureState({ source: COLUMNS, id: selectedColumn }, { selected: true })
}
watch(pr.selectedId, selectColumn)

// --- "Drop your site": tap the map once results are showing ---------------------
let siteMarker: Marker | null = null
function onMapClick(e: MapMouseEvent) {
  if (radial.value) return closeRadial()
  if (!cases.value.length || !pr.result.value?.proposal.homes) return
  pr.dropSite(e.lngLat.lng, e.lngLat.lat)
}
watch(pr.site, (site) => {
  const m = map.value
  if (!site || !m) {
    siteMarker?.remove()
    siteMarker = null
    return
  }
  if (!siteMarker) {
    const el = document.createElement('div')
    el.className = 'pr-drop'
    el.setAttribute('aria-label', 'Your site')
    el.innerHTML = '<div class="pr-drop__dot"></div>'
    siteMarker = new Marker({ element: el }).setLngLat([site.lng, site.lat]).addTo(m)
  }
  else siteMarker.setLngLat([site.lng, site.lat])
}, { deep: true })

// --- results → pins + framing ------------------------------------------------

function frameCases() {
  const m = map.value
  const points = cases.value.filter(inIreland).map(lngLat)
  if (!m || !points.length) return
  clearBuildingHighlight(m)
  if (points.length === 1) flyToProperty(m, points[0]!, { desktop: desktop.value, flat: true })
  else fitPoints(m, points, desktop.value)
}

function syncCases() {
  pins?.setCases(cases.value)
  syncColumns()
  syncPinState()
  // Stop the search orbit first; stopping it later would cancel the framing ease mid-flight.
  stopOrbit?.()
  stopOrbit = null
  requestAnimationFrame(frameCases)
}
watch(cases, syncCases)

function syncPinState() {
  pins?.setState({ selectedId: pr.selectedId.value, hoveredId: hovered.value })
}
watch([pr.selectedId, hovered], syncPinState)

// Orbit slowly over Dublin while the search runs.
const running = computed(() => pr.state.value === 'searching' && !cases.value.length)
watch(running, (now) => {
  const m = map.value
  if (!m) return
  if (now && !stopOrbit && !flat.value) stopOrbit = startOrbit(m, () => { stopOrbit = null })
  else if (!now) { stopOrbit?.(); stopOrbit = null }
})

// --- selection: fly in + building highlight ------------------------------------

let flyToken = 0
watch(pr.focusTick, () => {
  const m = map.value
  const c = pr.selectedId.value ? pr.caseById(pr.selectedId.value) : null
  if (!m || !c || !inIreland(c)) return
  stopOrbit?.()
  stopOrbit = null
  const t = ++flyToken
  clearBuildingHighlight(m)
  flyToProperty(m, lngLat(c), { desktop: desktop.value, flat: flat.value })
  m.once('moveend', async () => {
    if (t === flyToken && map.value) await highlightBuildingWhenSettled(m, lngLat(c))
  })
})
// Back from a case to the results: show them all again.
watch(pr.selectedId, (id, prev) => { if (!id && prev) frameCases() })

// --- radial menu (right-click / long-press, or tap the selected pin again) ---

const radial = ref<{ x: number; y: number; lngLat: { lng: number; lat: number }; caseId: string | null } | null>(null)
const radialRef = ref<InstanceType<typeof RadialMenu> | null>(null)

const radialItems = computed<RadialItem[]>(() => {
  const c = radial.value?.caseId ? pr.caseById(radial.value.caseId) : null
  if (c) {
    return [
      { key: 'details', label: 'Case details', icon: FileText },
      c.link || c.authority === 'Dublin City Council'
        ? { key: 'record', label: 'Open council record', icon: ExternalLink }
        : { key: 'copy', label: 'Copy application number', icon: Copy },
      { key: 'streetview', label: 'Street View', icon: PersonStanding },
    ]
  }
  return [{ key: 'streetview', label: 'Street View here', icon: PersonStanding }]
})

function openRadial(point: { x: number; y: number }, at: { lng: number; lat: number }, caseId: string | null = null) {
  radial.value = { x: point.x, y: point.y, lngLat: { lng: at.lng, lat: at.lat }, caseId }
}

function openRadialOnPin(id: string, point: { x: number; y: number }) {
  const c = pr.caseById(id)
  // Centre the ring on the pill, which sits ~22 px above the pin's tip.
  if (c && inIreland(c)) openRadial({ x: point.x, y: point.y - 22 }, lngLat(c), id)
}

function closeRadial() {
  radialRef.value?.close()
}

async function onRadialPick(key: string) {
  const r = radial.value
  if (!r) return
  const c = r.caseId ? pr.caseById(r.caseId) : null
  if (key === 'details' && c) pr.selectCase(c.id, false)
  else if (key === 'record' && c) {
    if (c.link) return void window.open(c.link, '_blank', 'noopener')
    // Open the tab inside the click so it isn't blocked, then point it at the resolved page.
    const tab = window.open('about:blank', '_blank')
    const url = await councilLink(c)
    if (url && tab) tab.location.href = url
    else {
      tab?.close()
      toast(c.id, { description: 'Search this number on the council\'s planning site.' })
    }
  }
  else if (key === 'copy' && c) {
    try {
      await navigator.clipboard.writeText(c.id)
      toast(`Copied ${c.id}`, { description: 'Search it on the council\'s planning site.' })
    } catch {
      toast(c.id, { description: 'Search this number on the council\'s planning site.' })
    }
  }
  else if (key === 'streetview') {
    window.open(`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${r.lngLat.lat},${r.lngLat.lng}`, '_blank', 'noopener')
  }
}

// --- controls (MapControls talks to the map through shared UI state) ----------

watch(flat, isFlat => map.value?.easeTo({ pitch: isFlat ? 0 : PITCH_3D, duration: 600 }))
watch(ui.zoomBy, (req) => {
  if (req) map.value?.easeTo({ zoom: map.value.getZoom() + req.delta, duration: 300 })
})
watch(ui.recentre, () => {
  const m = map.value
  if (!m) return
  if (cases.value.length) frameCases()
  else m.flyTo({ center: DUBLIN_CENTER, zoom: 11.5, pitch: flat.value ? 0 : CAMERA.browse.pitch, padding: { left: 0, right: 0, top: 0, bottom: 0 } })
})
</script>

<template>
  <div class="absolute inset-0">
    <!-- isolate: pin z-indexes stay inside the map, so menus and cards always sit above them. -->
    <div ref="container" class="isolate h-full w-full" />
    <RadialMenu
      v-if="radial"
      :key="`${radial.x},${radial.y}`"
      ref="radialRef"
      :x="radial.x"
      :y="radial.y"
      :items="radialItems"
      :hub="!radial.caseId"
      @pick="onRadialPick"
      @closed="radial = null"
    />
  </div>
</template>
