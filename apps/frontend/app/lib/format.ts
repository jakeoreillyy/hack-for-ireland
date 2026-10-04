const dayFormat = new Intl.DateTimeFormat('en-IE', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })

/** "2026-05-12" → "12 May 2026" */
export function day(value: string): string {
  return dayFormat.format(new Date(value)).replace('Sept', 'Sep')
}
