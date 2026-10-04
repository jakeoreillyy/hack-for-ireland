# API contract — `POST /predict`

Frozen per `planning-predictor-plan.md` → "Working concurrently" → "API contract". This file is the copy everyone codes against; if a field needs to change, edit it here and in that section together, and say so in the team chat first.

## Request

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

## Response

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

- `warnings` is always present: a list of short strings (e.g. `"Small sample: only 6 similar applications."`), empty array when there's nothing to flag.
- Nullable fields: `parsed.units` and `parsed.storeys` (not found in the text); every `stats` field except `n_similar` (all `null` when `n_similar` is 0); and in `matches`, `address`, `units`, `storeys`, `decision_date` and `link` (about 15% of applications have no link).
- `grant_rate` (in `stats`, `site_estimate` and `alternatives`) is the share of decided (granted or refused) applications that were granted. `n_similar` also counts invalid and withdrawn ones, so don't show it as "X% of `n_similar` were granted".
- `delay_factors` has 0–2 entries (a factor is left out when no similar application has a duration for it), `matches` up to 5 (closest in size first), `alternatives` up to 3 (most weeks saved first).
- Field names are final. Role 3 codes directly against these keys in `apps/frontend/mock/response.json`. The backend tests check the response's field names against the examples in this file.
