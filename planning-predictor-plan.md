# Planning permission predictor

A hackathon project for Build for Ireland (Dogpatch Labs, one-day build, 12:00 to 16:00).

## The idea

Ireland needs more apartments, but nobody planning one can easily tell how the planning process is likely to go. This tool answers three questions from public data:

- Will it be granted?
- How long will it take?
- What is likely to slow it down?

The user describes a project in plain English and picks a council. The tool finds similar past applications in the national planning register and shows what happened to them, with links to the real cases.

## Example

**Input:** "120 apartments in an 8-storey block near Heuston Station, with ground-floor retail", Dublin City Council.

**Output (numbers below are made up to show the format):**

- What we understood: apartments, 120 units, 8 storeys, mixed use, Dublin City
- 43 similar applications since 2018
- 70% granted, typical decision in 14 weeks, 33% appealed
- Delay factors: a further information request added N weeks; an appeal added N weeks
- A two-sentence plain-English summary
- Closest matches, each linking to the council's page for that application

### Faster-site suggestion

The user can drop a pin for the proposed site. The tool estimates the time to a decision there, then looks for nearby places where similar applications were decided faster, and suggests one.

**Example (numbers made up):** "Your site: typical decision about 2 years (104 weeks) including further information and appeals, based on 38 similar applications within 3 km. Alternative: 12 km away, in South Dublin, typical decision about 1 year (52 weeks), based on 27 similar applications. Faster by about 52 weeks."

How it works:

1. Take the pin as ITM coordinates (convert from lat/lon with `pyproj`).
2. Estimate the proposed site: median total days (decision, plus appeal where one happened) for similar applications within a radius, default 3 km, widened if fewer than 15 match.
3. Build candidate places: a grid of centres (about 2 km apart) within the user's maximum distance, default 25 km. Compute the same estimate for each, using only candidates with 15 or more similar applications.
4. Keep candidates that beat the proposed site by a meaningful margin (default 25% or at least 12 weeks) and rank by weeks saved, then by distance.
5. Show the top three: distance and direction, estimated time, weeks saved, grant rate, sample size, link to example applications.

It must be framed carefully:

- This compares what happened to past applications in each area. It does not say a site is suitable, zoned correctly, or that a decision will be faster.
- Grant rate must be shown next to speed. A faster area with a much lower grant rate is not a better option, so flag it.
- Council is usually the biggest driver of timing, so most suggestions will be across a council boundary. Say so on screen.
- Always show the sample size and warn when it is small.

## Where the data comes from

- **Source:** Department of Housing, Local Government and Heritage, national planning register, layer "Planning Application Points". It merges the planning registers of participating local authorities and covers applications received since 2012.
- **API:** `https://services.arcgis.com/NzlPQPKn5QF9v2US/arcgis/rest/services/IrishPlanningApplications/FeatureServer/0`
- **Catalogue page:** https://data.gov.ie/dataset/planning-application-sites1
- **Licence:** Creative Commons Attribution 4.0. Credit the Department on screen.

### Fields we use

| Need                      | Field                                                                         |
| ------------------------- | ----------------------------------------------------------------------------- |
| What was proposed         | `DevelopmentDescription`                                                      |
| Where                     | `PlanningAuthority`, `DevelopmentAddress`, `ITMEasting`, `ITMNorthing`        |
| Size                      | `NumResidentialUnits`, `FloorArea`, `AreaofSite`                              |
| Outcome                   | `Decision`                                                                    |
| Time taken                | `ReceivedDate`, `DecisionDate`, `DecisionDueDate`                             |
| Further information delay | `FIRequestDate`, `FIRecDate`                                                  |
| Appeals                   | `AppealStatus`, `AppealDecision`, `AppealSubmittedDate`, `AppealDecisionDate` |
| Link to the full file     | `LinkAppDetails`                                                              |

### Known limits

- There is no field for why an application was refused.
- There is no field for height or storeys. We extract storeys from the description text with a model.
- The `Decision` field has dozens of spelling variants. We map them into four groups: granted, refused, invalid, withdrawn.
- We have confirmed the fields exist but not how completely they are filled in. This is the first thing to check.
- The dataset includes applicant names and addresses. Drop those columns on load.
- The faster-site suggestion needs coordinates. We have not checked how many apartment rows have valid `ITMEasting` and `ITMNorthing`. Check this early; if it is poor, compare at council level instead of by distance.

### Do we need an LLM API?

Not strictly. The core numbers (matching, grant rate, timings, delay factors, site comparison) are plain SQL and Python. The model is used in four places, and each has a non-LLM fallback:

| Use | Needed? | Fallback without an API |
| --- | --- | --- |
| Tag storeys and mixed use from descriptions (prep) | Helpful, not essential | Regex for "8 storey", "eight-storey", "mixed use", "retail", "commercial". Run it first and send only the unmatched rows to a model. |
| Parse the user's sentence (live) | Only for the plain-English demo | A form with units, storeys, mixed use and a council dropdown |
| Write the summary (live) | No | A fixed template filled with the computed numbers. This is also safer, since it cannot invent figures. |
| Chat box (stretch) | No | Drop it |

Recommendation: keep the model for sentence parsing and for tagging the leftover descriptions, and use a template for the summary. That keeps the "describe it in plain English" demo, cuts per-query cost and latency, and means the tool still works if the API or wifi fails. Build the form first so the demo never depends on the API.

## How it works

### Prep (run once, before the demo)

1. Download the register and filter to descriptions that mention apartments.
2. Drop the applicant columns.
3. Normalise `Decision` into four groups.
4. Use an OpenAI model with a fixed JSON schema to tag each description with storeys and mixed use. Use `NumResidentialUnits` for units, falling back to the description where it is empty.
5. Compute days to decision, a further information flag and duration, and an appeal flag and duration.
6. Save one table (SQLite or Parquet) and keep a local copy.

### Live (per query)

1. **Parse:** the model turns the user's sentence into the same JSON structure.
2. **Match:** a SQL filter finds similar applications (same council, units and storeys within a band). Widen the bands if fewer than about 20 match.
3. **Aggregate:** grant rate, median days to decision, share with a further information request, share appealed, and the difference in days for each delay factor.
4. **Suggest (if a pin was dropped):** estimate the proposed site, scan nearby candidate places, and return up to three faster alternatives (see "Faster-site suggestion").
5. **Explain:** a short summary written only from the computed numbers (template by default, model optional), so it cannot invent figures.
6. **Display:** parsed details, stats, delay factors, summary, closest matches, and the faster-site suggestions on the map.

## Working concurrently

The three roles only stay independent if two things are nailed down **before** anyone splits up: the shape of the data table, and the shape of the API response. Everything below exists so Role 2 and Role 3 can start building against fake data at 12:00 instead of waiting on Role 1's real pipeline.

**First 15 minutes, all three together:** read and agree `CONTRACT.md` and the data schema below. Do not start coding solo until everyone has seen the final version. Treat both as frozen after that — if a field must change mid-afternoon, say so out loud before editing either file, since both other roles are coding against it.

### Repo layout

Each role owns a folder and does not edit another role's folder. The only shared files are `CONTRACT.md` and `data/schema.md`, and those are frozen after the first 15 minutes, so there is nothing left to collide on.

```
/data
  prep.py                  # Role 1: full pipeline, run once
  tag_descriptions.py      # Role 1: LLM tagging job (storeys, mixed use)
  fake_sample.csv          # Role 1: 10 made-up rows matching schema.md, first 15 min
  applications.parquet     # Role 1: real output, replaces the fake sample when ready
  schema.md                # the data contract below, kept in sync with prep.py

/apps/backend              # Role 2 (Python package, run instructions in README.md)
  pyproject.toml
  .env.example             # ANTHROPIC_API_KEY=... (placeholder only, never a real key)
  src/planning_predictor/
    main.py  config.py  schemas.py  repository.py
    api/routes.py          # single POST /predict endpoint
    services/              # parsing, matching, alternatives, summary, prediction
  tests/

/apps/frontend             # Role 3
  (index.html / src/...)
  mock/response.json       # hand-written example matching CONTRACT.md exactly

CONTRACT.md                # frozen API request/response shape, see below
.gitignore                 # .env, __pycache__, node_modules, large data files
```

Role 2's `repository.py` reads whichever file exists (`applications.parquet` if present, else `fake_sample.csv`) so it keeps working the moment Role 1 swaps the real data in — no code change needed on handoff.

### Git workflow

- Branch per role: `data`, `backend`, `frontend`, off `main`.
- Commit early and often on your own branch — nobody else is touching your folder, so there is nothing to conflict with.
- Open a PR into `main` at each checkpoint in the schedule below (12:30, 14:30, 15:45) rather than one big PR at the end, so a broken merge is caught early and is small to fix.
- If you must touch a file outside your folder (e.g. a shared constant), say so in the team chat first and keep the change to one line.
- Never force-push over someone else's branch.

### API contract (`CONTRACT.md`) — freeze by 12:30

One endpoint, `POST /predict`.

**Request**

```json
{
  "description": "120 apartments in an 8-storey block near Heuston Station, with ground-floor retail",
  "council": "Dublin City Council",
  "location": { "lat": 53.3467, "lon": -6.2947 },
  "max_distance_km": 25
}
```

`location` and `max_distance_km` are optional. Without `location` the response has no `site_estimate` or `alternatives` (return `null` and `[]`). `max_distance_km` defaults to 25.

`parsed_override` is also optional: `{ "units": 120, "storeys": 8, "mixed_use": true }`, any field omitted or `null`. The fallback form sends it to skip text parsing, and `description` may then be `""`. Invalid input (e.g. `lat` outside −90 to 90) gets HTTP 422.

**Response**

```json
{
  "parsed": {
    "units": 120,
    "storeys": 8,
    "mixed_use": true,
    "council": "Dublin City Council"
  },
  "stats": {
    "n_similar": 43,
    "grant_rate": 0.70,
    "median_days_to_decision": 98,
    "share_further_information": 0.35,
    "share_appealed": 0.33
  },
  "delay_factors": [
    { "factor": "further_information_request", "added_days": 28 },
    { "factor": "appeal", "added_days": 140 }
  ],
  "site_estimate": {
    "radius_km": 3,
    "n_similar": 38,
    "median_total_days": 728,
    "grant_rate": 0.66
  },
  "alternatives": [
    {
      "label": "Near Clondalkin, South Dublin",
      "council": "South Dublin County Council",
      "lat": 53.32,
      "lon": -6.39,
      "distance_km": 12,
      "direction": "W",
      "radius_km": 3,
      "n_similar": 27,
      "median_total_days": 364,
      "grant_rate": 0.72,
      "weeks_saved": 52,
      "warnings": []
    }
  ],
  "summary": "Two plain-English sentences, generated only from the numbers above.",
  "matches": [
    {
      "id": "DCC-2021-1234",
      "address": "Example St, Dublin 8",
      "units": 110,
      "storeys": 8,
      "decision": "GRANTED",
      "decision_date": "2023-05-01",
      "link": "https://..."
    }
  ],
  "warnings": []
}
```

- `warnings` is a list of short strings, e.g. `"Small sample: only 6 similar applications."` Always present, empty array when there's nothing to flag. This is how Role 2 communicates the small-sample and fallback cases from "Known limits" without changing the response shape.
- Nullable fields: `parsed.units` and `parsed.storeys` (not found in the text); every `stats` field except `n_similar` (all `null` when `n_similar` is 0); and in `matches`, `address`, `units`, `storeys`, `decision_date` and `link` (about 15% of applications have no link).
- `grant_rate` (in `stats`, `site_estimate` and `alternatives`) is the share of decided (granted or refused) applications that were granted. `n_similar` also counts invalid and withdrawn ones, so don't show it as "X% of `n_similar` were granted".
- `delay_factors` has 0–2 entries (a factor is left out when no similar application has a duration for it), `matches` up to 5 (closest in size first), `alternatives` up to 3 (most weeks saved first).
- Field names are final. If a name needs to change, update this file first and flag it in chat — Role 3 is coding directly against these keys.
- Role 3 builds `mock/response.json` as one concrete example of this exact shape and points the UI at it until the real endpoint exists, then swaps the base URL — no other frontend change needed.

### Data schema (`data/schema.md`) — Role 1 → Role 2 handoff

One table, one row per planning application. Role 2 writes `matching.py` against this schema using `fake_sample.csv` before the real pipeline is done.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | string | application reference, from `LinkAppDetails` or similar |
| `council` | string | from `PlanningAuthority` |
| `address` | string | from `DevelopmentAddress` |
| `units` | int | from `NumResidentialUnits`, falls back to tagged value |
| `storeys` | int or null | tagged from description, null if not extractable |
| `mixed_use` | bool | tagged from description |
| `decision` | enum | one of `granted`, `refused`, `invalid`, `withdrawn` |
| `received_date` | date | |
| `decision_date` | date or null | |
| `days_to_decision` | int or null | `decision_date - received_date` |
| `fi_requested` | bool | further information request flag |
| `fi_added_days` | int or null | |
| `appealed` | bool | |
| `appeal_added_days` | int or null | |
| `link` | string | URL to the council's page for that application |
| `itm_easting` | float or null | from `ITMEasting`, needed for the faster-site suggestion |
| `itm_northing` | float or null | from `ITMNorthing` |
| `total_days` | int or null | `days_to_decision` plus `appeal_added_days` where appealed; the figure used for site comparison |

If a column name or type changes, update `data/schema.md` and `CONTRACT.md` together in the same message to the team — they describe the same numbers at two different stages of the pipeline.

## The three roles

### Role 1: data

Owns the prep pipeline. This is the critical path, so it starts first.

- First 15 minutes: write `data/fake_sample.csv`, 10 made-up rows matching `data/schema.md`, and commit it — this is what unblocks Role 2 and Role 3
- Load and filter the register, check fill rates
- Normalise decisions and compute timings
- Run the tagging job
- Produce the delay factor numbers
- Keep `itm_easting`, `itm_northing` and `total_days`, and report how many apartment rows have valid coordinates
- Pick three demo examples that return good results
- Replace `fake_sample.csv` with the real `applications.parquet` once ready, keeping the same columns

### Role 2: model and backend

Owns the prompts and the single endpoint the front end calls.

- Parsing prompt and JSON schema, tested on real descriptions
- Matching query and aggregation
- Summary prompt that uses only computed numbers
- Fallback behaviour when few applications match
- Faster-site search in `alternatives.py`: radius stats, candidate grid, ranking, warnings

### Role 3: front end and demo

Owns the screen and the presentation.

- Build the single screen against mock JSON, then connect to the real endpoint
- Input form, stats cards, delay factors, closest matches with links
- Map with a draggable pin and the suggested alternatives, plus a "your site vs alternative" card
- Record a backup video of the working demo
- Rehearse and deliver the pitch

## Schedule

| Time           | Role 1: data                         | Role 2: model and backend         | Role 3: front end and demo   |
| -------------- | ------------------------------------ | --------------------------------- | ---------------------------- |
| 12:00 to 12:30 | Load, filter, check fill rates       | Parsing prompt and schema         | Screen against mock JSON     |
| 12:30 to 13:00 | Normalise decisions, compute timings | Test parsing on 20 descriptions   | Input form and stats cards   |
| 13:00 to 13:30 | Lunch (tagging job running)          | Lunch                             | Lunch                        |
| 13:30 to 14:30 | Finish tagging, save the table       | Matching and aggregation endpoint | Closest matches list         |
| 14:30 to 15:15 | Delay factor numbers, coordinate check | Faster-site search, summary template | Pin and alternatives on the map, connect to the real endpoint |
| 15:15 to 15:45 | Choose demo examples                 | Bug fixes and fallbacks           | Polish, record backup video  |
| 15:45 to 16:00 | Submit                               | Submit                            | Rehearse the pitch           |

**Go or no-go at 12:30.** If fill rates are poor, narrow to Dublin's four councils or match on units only and drop storeys. If coordinates are mostly missing, make the faster-site suggestion a council-level comparison instead of a distance search.

## Build order

1. Similar applications and grant rate
2. Predicted time to decision
3. Delay factors with days lost
4. Faster-site suggestion from a dropped pin
5. Chat box over the results (if time allows)
6. Compliance check against the 2025 apartment standards (stretch goal only)

Steps 1 to 3 are one pipeline and make a complete demo on their own. Step 4 is the best second demo moment, so build it before the chat box. If it is not working by 15:15, cut it and keep the rest.

## Presenting it

- Show the number of similar applications behind every figure, and warn when it is small.
- Word the delay figures as comparisons ("similar applications without a further information request were decided N weeks faster"), not as proof of cause.
- In the demo, type a tested example live, then click through to one real application on the council's site.
- Only quote numbers the tool actually produced.
- For the faster-site suggestion, say "similar applications in this area were decided faster", never "you will get permission faster". Show grant rate and sample size alongside it.
- Keep the processed data local and have the backup video ready in case the wifi fails.

## Before the day

- Push the repo skeleton: the folders under "Repo layout", an empty `CONTRACT.md` and `data/schema.md` with the tables above, `.gitignore`, `.env.example`, and three branches (`data`, `backend`, `frontend`).
- Download the data and check fill rates for apartment rows (decision, both dates, unit count).
- Confirm everyone has their OpenAI credits and API access working.
- Agree the JSON shape that the endpoint returns, so the front end can start against mock data.
