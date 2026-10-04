# Precedent (frontend)

See how similar housing proposals fared in planning, using Ireland's national planning register. Built for small builders and community housing groups at Build for Ireland, 4 October 2026.

Describe a proposal in plain English and pick a council. Precedent shows:

- the share of decided similar applications that were granted, and the typical time to a decision
- what added time (further information requests, appeals), as comparisons, not causes
- the closest matching cases, on a 3D map and in a list, each linked to its council record
- a short plain-English summary written only from those figures

It is an evidence browser, not a predictor. It shows how past applications fared; it never says how yours will.

## Run locally

The app needs the planning API (`apps/backend`) running. From the repo root:

```sh
# terminal 1: the API (see apps/backend/README.md for setup)
cd apps/backend && uvicorn planning_predictor.main:app --reload

# terminal 2: this app
cd apps/frontend
npm install
cp .env.example .env     # only needed if the API is not at http://127.0.0.1:8000
npm run dev
```

Open the local URL Nuxt prints. `npm run typecheck` checks the types; `npm run build` makes a production build.

## How it fits together

There is no data or matching logic in this app. One call to the API does the work:

| Where | What |
| --- | --- |
| `app/lib/api/predict.ts` | The only code that talks to `POST /predict` (shape in the root `CONTRACT.md`). Maps the response onto the UI types. |
| `app/composables/usePrecedents.ts` | Search state shared by the panel, the map and the cards. |
| `app/lib/planning/types.ts` | UI types and the list of 31 councils. |
| `server/api/council-link.get.ts` | Looks up the council portal page for Dublin City Council cases, which have no link in the register. |

- **Search:** type a description, or tap one of the three examples. If the description has no number of homes, you're asked for one.
- **Cases:** click a case in the list or a pin on the map to fly to it.
- **Drop your site:** after a search, tap the map to see similar applications within a few kilometres and any faster nearby areas.
- **Compare:** "Compare with the Dublin councils" runs the same proposal against the four Dublin councils.
- **Share and print:** the page address holds the search, so a copied link reruns it. The print button gives a one-page brief.

## Data credit

National Planning Applications register, Department of Housing, Local Government and Heritage, via [data.gov.ie](https://data.gov.ie/dataset/planning-application-sites1). Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Base map © OpenFreeMap, OpenMapTiles, OpenStreetMap contributors.

## Limits

- Refusal reasons and appeal outcomes are not in the register.
- Matching is by council, number of homes, storeys and mixed use, not by site, design or policy.
- Past decisions on similar applications, not a prediction. Not planning or legal advice.
