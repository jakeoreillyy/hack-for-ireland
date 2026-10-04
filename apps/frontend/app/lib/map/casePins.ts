import { Marker, type Map as MlMap } from 'maplibre-gl'
import type { PlanningCase } from '~/lib/planning/contract'
import { gsap, reducedMotion } from '~/lib/motion'

export interface CasePinHandlers {
  hover: (id: string | null) => void
  select: (id: string) => void
  /** Right-click on a pin; `point` is in map-container pixels at the pin's tip. */
  context: (id: string, point: { x: number; y: number }) => void
}

interface Entry { marker: Marker; el: HTMLElement; pill: HTMLButtonElement }

/** "120 homes" price-pill markers (RentCheck's rc-pin), coloured by council decision. */
export class CasePins {
  private pins = new Map<string, Entry>()
  private map: MlMap
  private handlers: CasePinHandlers

  constructor(map: MlMap, handlers: CasePinHandlers) {
    this.map = map
    this.handlers = handlers
  }

  setCases(cases: PlanningCase[]) {
    const want = new Set(cases.map(c => c.id))
    for (const [id, p] of this.pins) {
      if (!want.has(id)) {
        p.marker.remove()
        this.pins.delete(id)
      }
    }
    const created: Entry[] = []
    for (const c of cases) {
      if (this.pins.has(c.id)) continue
      const entry = this.create(c)
      this.pins.set(c.id, entry)
      created.push(entry)
    }
    if (created.length > 1 && !reducedMotion()) {
      created.forEach(e => e.el.classList.remove('rc-pin--enter'))
      gsap.from(created.map(e => e.pill), {
        y: -12, autoAlpha: 0, duration: 0.45, ease: 'back.out(1.7)',
        stagger: Math.min(0.03, 0.6 / created.length), clearProps: 'transform,opacity,visibility',
      })
    }
  }

  setState({ selectedId, hoveredId }: { selectedId: string | null; hoveredId: string | null }) {
    for (const [id, p] of this.pins) {
      const selected = id === selectedId
      const hovered = id === hoveredId && !selected
      p.el.classList.toggle('is-selected', selected)
      p.el.classList.toggle('is-hovered', hovered)
      p.el.style.zIndex = selected ? '30' : hovered ? '20' : '1'
    }
  }

  destroy() {
    for (const p of this.pins.values()) p.marker.remove()
    this.pins.clear()
  }

  private create(c: PlanningCase): Entry {
    const el = document.createElement('div')
    el.className = 'rc-pin rc-pin--enter'
    el.dataset.status = c.status
    el.classList.toggle('is-appealed', c.appealed === true)
    const pill = document.createElement('button')
    pill.type = 'button'
    pill.className = 'rc-pin__pill'
    pill.textContent = c.homes ? `${c.homes} homes` : c.id
    pill.setAttribute('aria-label', `${c.id}, ${c.title}, ${c.decisionLabel}, ${c.year}`)
    el.appendChild(pill)
    pill.addEventListener('mouseenter', () => this.handlers.hover(c.id))
    pill.addEventListener('mouseleave', () => this.handlers.hover(null))
    pill.addEventListener('click', (e) => {
      e.stopPropagation()
      this.handlers.select(c.id)
    })
    pill.addEventListener('contextmenu', (e) => {
      e.preventDefault()
      e.stopPropagation()
      this.handlers.context(c.id, this.map.project(c.coordinates))
    })
    el.addEventListener('animationend', () => el.classList.remove('rc-pin--enter'), { once: true })
    const marker = new Marker({ element: el, anchor: 'bottom' }).setLngLat(c.coordinates).addTo(this.map)
    return { marker, el, pill }
  }
}
