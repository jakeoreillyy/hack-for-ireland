# Agent 1: Data and API

**Before anything else, read `docs/agents/PRECEDENT_HANDOFF.md`.** It says what we're building, who owns which files, the API contract and the deadlines.

**Context in one line:** this repo was **RentCheck** (a rental checker). **We are transforming it into Precedent**, a planning precedent explorer. Everything in `server/` today is RentCheck legacy and gets replaced by you.

You own `frontend/server/**`, `frontend/scripts/**`, `frontend/app/lib/planning/contract.ts`, the `runtimeConfig` block in `frontend/nuxt.config.ts`, and `frontend/.env.example`. Do not edit anything else under `app/`; that's Agent 2's.

Your job: turn the national planning register into three reliable endpoints, so that Agent 2's screen shows real Dublin cases and the demo never depends on wifi or on OpenAI being up.

---

## Step 1: contract (by 14:25)

Create `app/lib/planning/contract.ts` by copying section 5 of the handoff **verbatim**. Run `npx nuxi typecheck` (or `npm run build` if that's quicker) to make sure it compiles. Post on the board:

`- [1→2] HH:MM READY contract.ts landed`

## Step 2: snapshot (by 14:35)

The live ArcGIS API is the source, but **the app reads a local snapshot**, which keeps the demo fast and offline-safe.

Write `scripts/build-snapshot.mjs` (plain Node, `fetch`, no new dependencies) that:

1. Queries the FeatureServer (URL in handoff section 6) for each of the four Dublin authorities with
   `where = PlanningAuthority='<name>' AND DevelopmentDescription LIKE '%apartment%' AND ReceivedDate >= DATE '2018-01-01'`,
   `outSR=4326`, `f=json`, and paginates with `resultOffset` / `resultRecordCount=2000`.
   - `outFields`: `ApplicationNumber, PlanningAuthority, DevelopmentDescription, DevelopmentAddress, NumResidentialUnits, Decision, ReceivedDate, DecisionDate, FIRequestDate, AppealStatus, AppealDecision, LinkAppDetails`. **Never request `Applicant*` fields.**
2. Normalises each row into a `PlanningCase` (without `match`):
   - **homes**: regex on the description first (`(\d+)\s*(no\.?\s*)?(apartments|residential units|units|dwellings|homes)`, take the largest). Use `NumResidentialUnits` only when the authority is **not** Dublin City Council and the regex found nothing. **Drop rows with fewer than 10 homes or no homes.**
   - **storeys**: regex for `(\d+|one|two|three|...|twenty)[- ]storey`, take the max. `null` if none.
   - **mixedUse**: description mentions retail, commercial, café, restaurant, office, creche, community or similar.
   - **status**: trim and upper-case `Decision`. `GRANT*` or `SPLIT*` → `granted` (label "Split decision" for split). `REFUSE*` → `refused`. Empty, null or `ADDITIONAL INFORMATION` → `pending`. `*INVALID*`, `*INVA`, `*WITHDRAWN*` → **drop the row**.
   - **weeks**: `round((DecisionDate - ReceivedDate) / 7 days)` when both exist and status isn't pending.
   - **furtherInfo**: `FIRequestDate != null`.
   - **appealed**: `null` for Dublin City Council (no appeal data published). Otherwise `!!AppealStatus?.trim()`.
   - **link**: `LinkAppDetails` or `null`.
   - **description**: strip a leading applicant-name clause (e.g. `^We,? .*? intend to apply` or `^.*? (Ltd|Limited|DAC)?,? intend(s)? to apply for permission`). Keep it simple; if the regex is unsure, keep the text.
   - **title**: a short title made by rule from the parsed fields, e.g. "124 apartments, 8 storeys, mixed use". No names.
3. Writes `server/data/precedents.json` as `{ snapshotDate, cases: PlanningCase[] }` and prints counts per authority and per status.

Run it, check the counts look sane (hundreds of rows, not thousands; most decided), and **spot-check five rows by eye** against the descriptions. Commit nothing; the user commits.

**Fallback:** if the API is down or slow, cut to Dublin City + South Dublin only. Do not skip the snapshot.

## Step 3: `/api/precedents` (by 14:35)

`server/api/precedents.get.ts`. Load the snapshot once (module-level import or `useStorage`), then:

1. Validate `authority` (one of `AUTHORITIES`) and `homes` (positive integer). 400 with the error shape otherwise.
2. **Match:** same authority, homes in `[0.5×, 2×]`, and if `storeys` given, storeys within ±2 or unknown. If fewer than 15 matches, widen homes to `[0.25×, 4×]` and drop the storeys filter, and set `widened: true`.
3. **Score** each match 0 to 100: closeness of homes (log ratio), storeys if both known, mixed use agreement, small recency bonus. Sort descending; return the top 25 as `cases`.
4. **Stats over all matches** (not only the 25), per the `PrecedentStats` comments. `grantRate` is `null` if fewer than 3 decided. `appealShare` is `null` for Dublin City Council.
5. `matchRule`: plain English describing what was actually applied.
6. `source`: as in the contract, `snapshotDate` from the file.

Post `READY /api/precedents` with a sample curl and the counts it returns for the default demo proposal (120 homes, 8 storeys, mixed use, Dublin City Council).

## Step 4: `/api/parse` and `/api/explain` (by 15:00)

Add `runtimeConfig: { openaiApiKey: '', openaiModel: '' }` in `nuxt.config.ts` (server-only, so **not** under `public`). Document `NUXT_OPENAI_API_KEY=` and `NUXT_OPENAI_MODEL=` in `.env.example`. Use plain `$fetch` to the OpenAI API with a JSON schema response format; don't add the SDK unless it's already installed. Pick the model the team's event credits cover and put it in `.env`.

**`POST /api/parse`** `{ description }` → `ParsedProposal`.
- With a key: the model fills `homes`, `storeys`, `mixedUse` and `kind` from the text, using a strict JSON schema. `source: 'ai'`.
- Without a key, on error, or after a 6-second timeout: run the **same regexes as the snapshot script** (share them via `server/utils/parse.ts`). `source: 'rules'`.

**`POST /api/explain`** `{ proposal, stats, cases }` → `ExplainResponse`.
- Prompt with **only** the stats object, the match rule and the top 5 cases (id, homes, storeys, status, weeks). Instruct it to write at most 3 sentences, to use only the numbers given, to cite case ids in square brackets, to phrase further-info effects as comparisons and not causes, and never to predict an outcome.
- After the response: keep only `citedIds` that exist in `cases`. If the text contains a number that isn't in the stats or the cases, discard it and use the template.
- **Template fallback** (no key, error, 8-second timeout): build the sentence from the stats in code, e.g. "Of 31 similar applications to Dublin City Council since 2018, 22 were granted and 6 refused. Decided cases typically took 14 weeks. Those with a further information request took a median of 9 weeks longer." `source: 'template'`.

Post `READY /api/parse, /api/explain` with one example output of each.

## Step 5: clean out RentCheck (by 15:10)

Delete the RentCheck server code: `server/api/analyse.post.ts`, `server/api/analysis/**`, `server/api/listings/**`, `server/api/commute.get.ts`, `server/api/geocode.get.ts`, `server/fixtures/**`. Keep `server/utils/api-error.ts` only if you use it. Run `npm run build` and post the result. If the build fails because of an `app/` file importing something you removed, post `ASK` to Agent 2. Don't fix their files.

## Step 6: demo examples (by 15:15)

Run the endpoints for candidate proposals across councils and pick **three** that return 15 or more matches with a mix of granted and refused. Prefer at least one South Dublin example, since it has case links and appeal data, so the demo can click through to a real council page. Post the three descriptions and the counts they produce. Agent 2 puts them in the UI as example chips.

## Done means

- `npm run build` passes.
- All three endpoints work **with the OpenAI key removed from `.env`** (fallbacks), and with it present.
- No `Applicant*` field anywhere in the snapshot.
- Every number the UI shows can be traced to the snapshot.
- Final board entry: files changed, how to regenerate the snapshot, known data gaps.
