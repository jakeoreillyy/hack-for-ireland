// Regex rules for reading planning descriptions. Shared by the Nitro server
// (/api/parse fallback) and scripts/build-snapshot.mjs (Node runs .ts directly).

const WORDS: Record<string, number> = {
  one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
  eleven: 11, twelve: 12, thirteen: 13, fourteen: 14, fifteen: 15, sixteen: 16,
  seventeen: 17, eighteen: 18, nineteen: 19, twenty: 20,
}

function num(token: string): number {
  const t = token.toLowerCase()
  return WORDS[t] ?? Number.parseInt(t, 10)
}

const HOMES_RE = /(\d{1,4})\s*(?:no\.?|number|nr\.?)?\s*(?:\(\s*\d+\s*\)\s*)?(?:new\s+)?(?:residential\s+)?(?:build[- ]to[- ]rent\s+)?(?:apartments?|apartment units|residential units|units|dwellings?|homes|duplex(?:es)?|houses)\b/gi

/** Largest home count mentioned in the text, or null. */
export function extractHomes(text: string): number | null {
  if (!text) return null
  let best: number | null = null
  for (const m of text.matchAll(HOMES_RE)) {
    const n = Number.parseInt(m[1]!, 10)
    if (n > 0 && n < 5000 && (best === null || n > best)) best = n
  }
  return best
}

const STOREY_RE = /\b(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s*(?:-|\s)?\s*stor(?:e)?y/gi

/** Tallest storey count mentioned, or null. */
export function extractStoreys(text: string): number | null {
  if (!text) return null
  let best: number | null = null
  for (const m of text.matchAll(STOREY_RE)) {
    const n = num(m[1]!)
    if (n > 0 && n <= 50 && (best === null || n > best)) best = n
  }
  return best
}

const MIXED_RE = /\b(retail|commercial|caf[eé]|restaurant|office|cr[eè]che|childcare|community (?:space|facility|facilities|use|room)|shop|gym|co-working|coworking|licensed premises)\b/i

export function isMixedUse(text: string): boolean {
  return !!text && MIXED_RE.test(text)
}

export function extractKind(text: string): string {
  if (!text) return 'Apartments'
  if (/student accommodation/i.test(text)) return 'Student accommodation'
  if (/build[- ]to[- ]rent|\bBTR\b/i.test(text)) return 'Build-to-rent'
  if (/shared accommodation|co-living/i.test(text)) return 'Shared living'
  if (/apartment/i.test(text)) return 'Apartments'
  return 'Housing'
}

// Leading "We, X, intend to apply for permission..." or "X Ltd intends to apply..."
const APPLICANT_RE = /^[\s\S]{0,220}?\bintends?\s+to\s+apply\s+(?:to\s+[^.]{0,80}?\s+)?for\s+(?:an?\s+)?(?:\w+[- ]year\s+)?(?:planning\s+)?(?:permission|retention)[^.:]{0,20}?\s+(?:for\s+(?:(?:the\s+)?development\s+)?(?:at\s+[^,]{0,80},?\s*)?)?/i

/** Strips a leading applicant-name clause so no names are shown. */
export function stripApplicant(text: string): string {
  if (!text) return ''
  const cleaned = text.replace(APPLICANT_RE, '').trim()
  if (cleaned.length < 20) return text.trim()
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
}

export function titleFor({ homes, storeys, mixedUse, kind }: { homes: number, storeys: number | null, mixedUse: boolean, kind: string }): string {
  const parts = [`${homes} ${kind === 'Apartments' || kind === 'Housing' ? 'homes' : kind.toLowerCase()}`]
  if (storeys) parts.push(`${storeys} storeys`)
  if (mixedUse) parts.push('mixed use')
  return parts.join(', ')
}
