# RentCheck → Planning Precedent Explorer: Transformation Plan

## Goal

Transform the existing RentCheck app into a Planning Precedent Explorer for residents and community groups. Reuse its Nuxt app shell, map, staged analysis flow, report layout and evidence UI. Replace the rental domain, fixtures and API behavior with Irish planning application data.

**Product pitch:** “See how similar housing proposals were decided by the same planning authority, with the official cases and an AI explanation behind every result.”

The app describes historical cases. It does not predict whether a new proposal will be granted or provide planning advice.

## What the team is building

A user selects a planning authority and proposal type, then enters a short description and (if supported by the data) the number of homes. The app:

1. Uses AI to turn the description into editable structured fields.
2. Finds comparable historic planning applications from the selected authority.
3. Calculates outcome counts and decision-time summaries deterministically.
4. Shows comparable cases, their recorded outcomes, dates and official source links.
5. Uses an **AI Case Explainer** to explain what the returned cases have in common, what outcomes and timelines they show, and where the evidence is weak.
6. Shows the same cases on the map when reliable coordinates are available.

Every AI statement must be grounded in returned records or computed figures and linked to its supporting case(s). AI must not invent counts, outcomes, statistics, causes or approval predictions. If there is too little evidence or AI is unavailable, show a clear limitation and keep the factual results usable.

## Reuse from the existing app

### Keep and adapt

- Nuxt/Vue shell and responsive panel layout
- MapLibre map lifecycle, selection and camera behavior
- Analysis stages and report navigation
- Evidence drawer, cards, tables and loading/error patterns
- Shared UI primitives, typography, map infrastructure and motion utilities

### Replace or remove

- Rental listing fixtures, listing search and rent-specific API contracts
- Rent verdicts, rent distribution/trend charts and property price pins
- Rental photos, landlord enquiry actions, commute-to-work tools and rent filters
- Rental language in labels, empty states, report sections and demo copy

Do not build new 3D building models for the MVP. Show planning case locations only when the records provide usable coordinates. If coordinate quality is poor, make the case list and report the primary experience.

## Three-person split

### Person 1 — Data, backend and AI

**Owns:** planning data retrieval/fixture, server API routes, shared API types, matching and calculations, AI endpoint.

1. **First 15 minutes: data gate.** Fetch a small sample from the national planning register. Check usable coverage for authority, proposal description, decision, received date, decision date, unit count and official record link.
2. Choose one planning authority and apartment proposals. Save a dated local sample with source attribution as a demo fallback.
3. Replace the rental fixtures and endpoints with a small planning application schema. Exclude applicant names and unnecessary personal details.
4. Implement deterministic matching on authority and proposal type; use a unit-count band only if coverage supports it. Return the matching rule, date range, record counts, comparable cases and calculations.
5. Normalize known decision labels while preserving unknown values. Compute decision-time summaries only from valid date pairs and include the denominator.
6. Implement proposal parsing and the **AI Case Explainer**. Give the model only the matched case summaries and computed results. Require a structured response whose claims reference case IDs or metric IDs. Validate references before returning them to the client.

**Deliverable:** API works from a proposal input to checked comparison data and evidence-referenced AI explanation.

### Person 2 — Product flow, report and AI experience

**Owns:** input form, panel flow, analysis progress, report components, evidence presentation and user-facing copy.

1. Replace the rental form with planning authority, development type, free-text description and optional unit count. Show parsed AI fields in an editable confirmation step.
2. Adapt the current stage UI to show real work: interpreting the proposal, finding comparable cases, calculating observed results and preparing the AI explanation.
3. Replace rental verdicts and charts with the matching criteria, record count/date range, observed decisions, decision-time summary, case list and source links.
4. Design an **AI Case Explainer** card. Make it clear which cases support each point; clicking a citation opens the matching case details/source. Distinguish the AI explanation from the underlying recorded facts.
5. Show thin evidence, unknown outcomes, missing dates, and AI service errors gracefully. Never present a confidence score or approval probability without a validated method.
6. Remove rental-only sections and check all visible labels, empty states, errors and print/report views for leftover rent language.

**Deliverable:** a complete proposal → progress → evidence-backed report flow, initially working against Person 1’s agreed fixture/API shape.

### Person 3 — Map, integration and demo

**Owns:** map-specific components/layers, end-to-end integration, manual verification and demo preparation.

1. Replace rental price pins with planning case markers from the shared application schema.
2. Display the proposed site and returned comparable cases when coordinates are reliable. Avoid implying proximity is part of the match unless distance is explicitly calculated.
3. Remove rental-specific layers and controls, including rent heat, commute tools, transport context and landlord actions.
4. Agree the API shape with Persons 1 and 2 early; use the same dated sample while live data and screens are built in parallel.
5. Connect selection on the map to the case list and evidence view. If the map adds no value for the sample, simplify it and focus on case evidence.
6. Rehearse a known query. Check that every displayed number agrees with the returned records, source attribution is visible, and AI citations open the correct cases.

**Deliverable:** one working end-to-end demo with map/case synchronization where data supports it, plus a rehearsed fallback using the dated sample.

## Shared contract to agree by 12:30

For each query, the backend should return:

- Parsed proposal fields and the matching rule
- Authority and data retrieval date
- Number of matching records and date range
- Outcome counts with denominators
- Median decision time with the valid-record count
- Comparable case IDs, descriptions, recorded decisions, dates, official links and optional coordinates
- AI explanation claims, each with supporting case IDs or metric IDs
- Coverage warnings and limitations

Keep calculations on the server. The browser should display the returned evidence without recomputing or inventing metrics.

## Four-hour schedule

| Time | Team focus | Checkpoint |
| --- | --- | --- |
| 12:00–12:15 | Everyone: fetch/inspect planning sample and pick one demo query | Data gate passed or pivot decision made |
| 12:15–12:30 | Agree schema, matching rule, API response and work boundaries | Shared fixture shape is stable |
| 12:30–13:00 | Person 1: data/API skeleton; Person 2: form/report shell; Person 3: map conversion | All three workstreams run against the fixture |
| 13:00–13:30 | Lunch / background data preparation | Keep the local sample ready |
| 13:30–14:30 | Connect real or dated data; implement deterministic match and report | Proposal input returns real cases and checked metrics |
| 14:30–15:15 | Add grounded AI Case Explainer and citation links; handle missing data | AI is visibly useful and claims trace to cases |
| 15:15–15:40 | Integrate map selection, source labels and error states | One end-to-end flow is stable |
| 15:40–16:00 | Rehearse, verify displayed numbers, prepare and submit | Demo is ready by the submission deadline |

## Data and AI go/no-go

If the planning register is unavailable or too sparse, first narrow to one authority and proposal type. Use a dated, source-credited local sample if the live service is unreliable. Do not fabricate planning results.

If AI parsing or explanation fails, preserve the working product: let the user edit the structured proposal fields and show the deterministic cases and metrics with a clear “AI explanation unavailable” message. The core AI feature should be attempted after retrieval and calculations work.

## Demo script

1. Enter a proposed apartment development and select its planning authority.
2. Show the AI-parsed fields and correct one if needed.
3. Start the analysis and show the stages as the app retrieves and compares past cases.
4. Open the report: show the number of cases, matching rule, observed outcomes and decision-time summary.
5. Read the AI Case Explainer and click a citation to inspect the official supporting case.
6. Show comparable cases on the map if coordinates are sound; otherwise keep attention on the cited case list.
7. Close with the limitation: these are historical comparisons to support understanding, not a forecast of a new decision.

## Definition of done

- The app no longer presents itself as a rental checker.
- One selected authority and proposal type return a useful set of real or clearly dated sample cases.
- Every statistic shows its denominator and source/date context.
- AI provides a visible plain-language comparison explanation whose claims cite returned evidence.
- The report remains useful if AI is unavailable or the dataset has gaps.
- The demo is rehearsed and ready for submission.
