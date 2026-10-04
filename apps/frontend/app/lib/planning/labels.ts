import { AUTHORITIES, type Authority, type DecisionStatus } from './contract'

// Display names: the register's name, except where Irish spelling differs (Agent 1, 15:05).
export const AUTHORITY_LABEL = Object.fromEntries(AUTHORITIES.map(a => [a, a])) as Record<Authority, string>
AUTHORITY_LABEL['Dun Laoghaire Rathdown County Council'] = 'Dún Laoghaire-Rathdown County Council'

// Agent 1's three tested examples (board, 14:20). Keep the strings exact.
export const EXAMPLES: { label: string; authority: Authority; description: string }[] = [
  { label: 'Heuston · 120 homes', authority: 'Dublin City Council', description: '120 apartments in an 8-storey block near Heuston Station, with ground-floor retail' },
  { label: 'Clondalkin · 120 homes', authority: 'South Dublin County Council', description: '120 apartments in a 6-storey scheme in Clondalkin with a creche and ground-floor cafe' },
  { label: 'Phibsborough · 60 homes', authority: 'Dublin City Council', description: '60 apartments in a 6-storey building in Phibsborough' },
]

/** Tailwind classes per council decision (RentCheck's planning tokens). */
export const STATUS_STYLE: Record<DecisionStatus, { dot: string; fill: string; text: string; soft: string }> = {
  granted: { dot: 'bg-planning-granted', fill: 'fill-planning-granted', text: 'text-planning-granted', soft: 'bg-planning-granted/10 text-planning-granted border-planning-granted/30' },
  refused: { dot: 'bg-planning-refused', fill: 'fill-planning-refused', text: 'text-planning-refused', soft: 'bg-planning-refused/10 text-planning-refused border-planning-refused/30' },
  pending: { dot: 'bg-planning-pending', fill: 'fill-planning-pending', text: 'text-planning-pending', soft: 'bg-planning-pending/10 text-planning-pending border-planning-pending/30' },
}

export function percent(value: number) {
  return `${Math.round(value * 100)}%`
}

export function weeksLabel(c: { weeks: number | null; status: DecisionStatus }) {
  if (c.weeks != null) return `${c.weeks} wks`
  return c.status === 'pending' ? 'Awaiting decision' : 'Weeks not recorded'
}
