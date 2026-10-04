# Precedent

See how similar housing proposals fared in planning, using Ireland's national planning register. Built for small builders and community housing groups at Build for Ireland, 4 October 2026.

Describe a proposal in plain English and pick a council. Precedent reads the description, finds similar past applications and shows:

- the share of decided similar applications that were granted, and the typical time to a decision
- what added time (further information requests, appeals), as comparisons, not causes
- the closest matching cases, on a 3D map and in a list, each linked to its council record
- a short plain-English summary written only from those figures

It is an evidence browser, not a predictor. It shows how past applications fared; it never says how yours will.

## Using it

- **Search:** type a description, or tap one of the three examples, then **Find similar applications**. If the description has no number of homes, you're asked for one.
- **Cases:** click a case in the list or a pin on the map to fly to it. The case card links to the council record. Dublin City Council publishes no links in the register, so those are looked up on the council's planning portal.
- **Drop your site:** after a search, tap the map to see similar applications within a few kilometres and any faster nearby areas.
- **Compare:** "Compare with the Dublin councils" runs the same proposal against the four Dublin councils.
- **Share and print:** the page address holds the search, so a copied link reruns it. The print button gives a one-page brief.

## Run locally

```sh
npm install
cp .env.example .env
npm run dev
```

Open the local URL Nuxt prints. For a production build, run `npm run build`.

### Data sources

- `NUXT_PREDICTOR_URL` points at the team's predictor backend (hack-for-ireland `apps/backend`, FastAPI on `:8000`). It covers all 31 councils and powers "Drop your site".
- With it unset or down, the API falls back to a local snapshot of the four Dublin councils in `server/data/precedents.json`. Rebuild it with `node scripts/build-snapshot.mjs`.
- No AI service key is needed. Parsing and summaries come from the predictor or from rules and templates.

## API

| Method | Path | Returns |
| --- | --- | --- |
| `POST` | `/api/parse` | homes, storeys and mixed use read from a description |
| `GET` | `/api/precedents` | stats and closest cases; add `lat` and `lon` for a site estimate |
| `POST` | `/api/explain` | the plain-English summary |
| `GET` | `/api/council-link?id=` | the council portal page for a Dublin City Council application number |

Types are in `app/lib/planning/contract.ts`.

## Data credit

National Planning Applications register, Department of Housing, Local Government and Heritage, via [data.gov.ie](https://data.gov.ie/dataset/planning-application-sites1). Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Base map © OpenFreeMap, OpenMapTiles, OpenStreetMap contributors.

## Limits

- Refusal reasons and appeal outcomes are not in the register.
- Matching is by council, number of homes, storeys and mixed use, not by site, design or policy.
- Past decisions on similar applications, not a prediction. Not planning or legal advice.
