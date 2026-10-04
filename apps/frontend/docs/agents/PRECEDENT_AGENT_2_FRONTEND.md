# Agent 2: Frontend

**Before anything else, read `docs/agents/PRECEDENT_HANDOFF.md`.** It says what we're building, who owns which files, the API contract and the deadlines.

**Context in one line:** this repo was **RentCheck** (a rental checker). **We are transforming it into Precedent**, a planning precedent explorer. The Precedent screen already exists (`PlanningWorkspace.vue` + `PrecedentMap.vue`), but it runs on 6 hard-coded synthetic cases. Your job is to put it on real data and remove what's left of RentCheck in `app/`.

You own `frontend/app/**` **except** `app/lib/planning/contract.ts`, plus `frontend/README.md` and `frontend/DESIGN.md`. You do not touch `server/**` or `scripts/**`; those are Agent 1's. Visual direction stays as in `frontend/DESIGN.md`. **Do not redesign.** Wire, fix and make it honest.

---

## Step 1: data layer against the contract (by 14:40)

Agent 1 lands `app/lib/planning/contract.ts` first (copied from handoff section 5). Until it exists, code against the types in the handoff.

Create `app/composables/usePrecedents.ts` (auto-imported, top-level `composables/`):

- `parse(description)` → `POST /api/parse`
- `search({ authority, homes, storeys, mixedUse })` → `GET /api/precedents`
- `explain(response)` → `POST /api/explain`
- Exposes reactive `state: 'idle' | 'parsing' | 'searching' | 'explaining' | 'done' | 'error'`, `parsed`, `result`, `explanation`, `error`.

Plain `$fetch` is fine; Vue Query is optional. **Until Agent 1 posts `READY /api/precedents`, use a local mock** that adapts `DEMO_CASES` into a `PrecedentsResponse`, behind one flag in the composable. Delete the mock as soon as the real endpoint is up.

## Step 2: wire the workspace (by 15:00)

In `PlanningWorkspace.vue`:

1. **Submit flow:** the button runs parse → search → explain in order, with a visible step state ("Reading your description", "Finding similar applications", "Writing summary"). Rename the button to something like "Find similar applications". Drop "Preview sample analysis".
2. **Parsed chips** come from `parsed`, not hard-coded "Mixed use". If `parsed.homes` is null, show an inline prompt to enter homes and don't search. The `Homes` input overrides the parsed value. Label the chips "AI read" when `source === 'ai'` and "Read by rules" when `'rules'`.
3. **Authority select:** enable all four from `AUTHORITIES`. Remove the "coming later" options.
4. **Metrics:** replace the three hard-coded cards (including the fake "3 km match range" and "18 wks") with `grantRate` (show "X of Y decided"), `medianWeeks`, and `furtherInfoShare`. Use `stats.total`, not `cases.length`, for counts. When a value is `null`, show "Not enough data" or, for appeals, "Not published by this council". Warn visibly when `stats.decided < 10`.
5. **Explainer card:** `explanation.text`, with citation chips from `citedIds` that select the case. Label "AI summary of the figures above" for `'ai'` and "Summary" for `'template'`. Remove the "SOURCED" check mark unless it's true.
6. **Further info line:** if `furtherInfoExtraWeeks` is set, show "Applications with a further information request took a median of N weeks longer". It's a comparison, not a cause.
7. **Case list:** from `result.cases`. Show id, title, location, year, homes, storeys, status, weeks and a "Further info" or "Appealed" tag where true. Clicking a row selects it and focuses the map (keep the existing `selectCase` and `focusCase` pattern). The search box filters the shown list only.
8. **Selected case card** (map overlay): status, weeks, description (clamped to 3 lines), and **"Open council record"** linking to `link` in a new tab. When `link` is null (all Dublin City Council cases), show the application number with "Search this number on the council's planning site" and no fake link.
9. **Status colours:** `DecisionStatus` is now `granted | refused | pending`, and `appealed` is a separate boolean. Update the dots, legend and `PrecedentMap.vue` paint expression. Show appealed as a ring or tag, not a fourth status colour.
10. **Map:** pass `result.cases`. After each search, fit the camera to the returned cases. The top card "Exploring area" shows the authority and `stats.total`, not "Dublin 8".
11. **Example chips:** under the textarea, add 3 clickable examples. Use placeholders until Agent 1 posts the tested three, then swap them in exactly.

## Step 3: honesty pass (by 15:15)

These are the things that make the demo trustworthy. Do all of them.

- **Remove every "DEMO DATA", "SAMPLE VIEW", "illustrative", "synthetic" and "not live" label from the real-data path.** Replace them with a source line: "National Planning Applications register · Dept. of Housing · CC BY 4.0 · snapshot {snapshotDate}", linking to `source.url`. This is a required data credit.
- Show `matchRule` near the count, and a "Bands widened: few close matches" note when `widened`.
- Keep the trust note, reworded: "Past decisions on similar applications, not a prediction. Refusal reasons and appeal outcomes are not in the register."
- Remove dead controls: "How it works" (unless you wire it to a short modal), the avatar button, the "Closest match" filter button, the map toolbar buttons, and the hard-coded "500 m" scale. Anything kept must do something.
- Error state: if `/api/precedents` fails, show a clear message with retry. Never fall back to demo cases silently.

## Step 4: remove RentCheck from `app/` (by 15:25)

Delete only after confirming nothing imports them (`grep`, then `npm run build`):

- `app/composables/api/**`, `app/types/api.ts`, `app/composables/useMapSelection.ts`, `app/plugins/vue-query.ts` (unless you used Vue Query)
- `app/lib/verdict.ts`, `beat.ts`, `photos.ts`, `transport.ts`, `schemas.ts`, `motion.ts` if unused
- `app/components/map/layers/PlanningLayer.vue`, `app/components/evidence/**` if unused
- Map helpers in `app/lib/map/` that `PrecedentMap.vue` doesn't reach (`pins`, `hex`, `saved`, `places`, `counties`, `building`, `layer`, `state`, `registry`). **Keep `core.ts`, `config.ts`, `worker.ts` and whatever they import.**
- `app/lib/planning/demo.ts` once nothing uses it.

Check that `app/app.vue` has no RentCheck leftovers (title, providers). Update `README.md` to describe Precedent on real data, how to set `NUXT_OPENAI_API_KEY`, and the data credit. Remove the "synthetic fixtures" paragraph.

## Step 5: verify (by 15:30, then freeze)

- `npm run build` passes. Report warnings separately from failures.
- Run all three example chips end to end in the browser at desktop width and at 375 px. Check: counts match between header, metrics and explainer; clicking a citation selects the case and moves the map; a South Dublin case opens its real council page.
- Run it once with the OpenAI key removed (ask Agent 1 or the user) and confirm the "Read by rules" and "Summary" labels appear and nothing breaks.
- Final board entry: files changed, what you deleted, what you verified and how, anything left unverified.

## Out of scope today

Login, saving proposals, drawing a site on the map, distance-based matching, compliance checks against apartment standards, chat. If there's spare time after 15:30, the answer is rehearse and record the backup video, not new features.
