// Rule-based reading of a proposal description: the /api/parse fallback.
import type { ParsedProposal } from '../../app/lib/planning/contract'
import { extractHomes, extractStoreys, isMixedUse, extractKind } from './rules'

export function parseByRules(description: string): ParsedProposal {
  return {
    homes: extractHomes(description),
    storeys: extractStoreys(description),
    mixedUse: isMixedUse(description),
    kind: extractKind(description),
    source: 'rules',
  }
}
