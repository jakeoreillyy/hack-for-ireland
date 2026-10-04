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

- `warnings` is always present: a list of short strings (e.g. `"Only 6 similar applications found — bands widened to show these."`), empty array when there's nothing to flag.
- Field names are final. Role 3 codes directly against these keys in `frontend/mock/response.json`.
