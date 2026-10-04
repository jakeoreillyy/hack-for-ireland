import { AUTHORITIES, type Authority, type DecisionStatus } from './types'

// Display names: the register's name, except where Irish spelling differs.
export const AUTHORITY_LABEL = Object.fromEntries(AUTHORITIES.map(a => [a, a])) as Record<Authority, string>
AUTHORITY_LABEL['Dun Laoghaire Rathdown County Council'] = 'Dún Laoghaire-Rathdown County Council'

// Tested against the real register (data/demo_examples.md). Keep the strings exact.
export const EXAMPLES: { label: string; authority: Authority; description: string }[] = [
  { label: 'Citywest · 150 homes', authority: 'South Dublin County Council', description: '150 apartments in a 10-storey block in Citywest, South Dublin' },
  { label: 'Naas · 90 homes', authority: 'Kildare County Council', description: '90 apartments in a 6-storey development near Naas, with ground-floor retail' },
  { label: 'Drogheda · 60 homes', authority: 'Louth County Council', description: '60 apartments in a 5-storey scheme in Drogheda, Co. Louth' },
]

/** Tailwind classes per decision status. */
export const STATUS_STYLE: Record<DecisionStatus, { dot: string; fill: string; text: string; soft: string }> = {
  granted: { dot: 'bg-planning-granted', fill: 'fill-planning-granted', text: 'text-planning-granted', soft: 'bg-planning-granted/10 text-planning-granted border-planning-granted/30' },
  refused: { dot: 'bg-planning-refused', fill: 'fill-planning-refused', text: 'text-planning-refused', soft: 'bg-planning-refused/10 text-planning-refused border-planning-refused/30' },
  closed: { dot: 'bg-planning-closed', fill: 'fill-planning-closed', text: 'text-planning-closed', soft: 'bg-planning-closed/10 text-planning-closed border-planning-closed/30' },
}

/** "South Dublin County Council" → "South Dublin". Falls back to the full name. */
export function shortCouncil(name: string) {
  return name.replace(/ (City and County|County|City) Council$/, '').replace(/ Council$/, '') || name
}

export function percent(value: number) {
  return `${Math.round(value * 100)}%`
}

export function weeksLabel(c: { weeks: number | null }) {
  if (c.weeks != null) return `${c.weeks} wks`
  return 'Weeks not recorded'
}
