# Data schema — `applications.parquet` / `fake_sample.csv`

Frozen per `planning-predictor-plan.md` → "Working concurrently" → "Data schema". One row per planning application. Role 2 writes `matching.py` against this using `fake_sample.csv` before the real pipeline (`prep.py`) is done; `matching.py` should read whichever file exists, preferring `applications.parquet`.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | string | application reference, from `ApplicationNumber` |
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
| `link` | string | URL to the council's page for that application, from `LinkAppDetails` |
| `itm_easting` | float or null | from `ITMEasting`, needed for the faster-site suggestion |
| `itm_northing` | float or null | from `ITMNorthing` |
| `total_days` | int or null | `days_to_decision` plus `appeal_added_days` where appealed; the figure used for site comparison |

If a column name or type changes, update this file and `CONTRACT.md` together in the same message to the team.

## Known from the live source (checked 2026-10-04, after running `prep.py` end to end)

- API: `https://services.arcgis.com/NzlPQPKn5QF9v2US/arcgis/rest/services/IrishPlanningApplications/FeatureServer/0`
- 508,657 rows total; 13,704 where `DevelopmentDescription` mentions "apartment" — our filtered set.
- `maxRecordCount` is 2000 per page; pagination (`resultOffset`/`resultRecordCount`) is supported, so `prep.py` pages through all ~13.7k rows in ~7 requests.
- `Decision` has 70+ spelling/case variants in the apartment subset alone (confirmed live, not just a guess — see the mapping in `prep.py`). A handful are not final decisions at all (`N/A`, `ADDITIONAL INFORMATION`, `Decision to be Made by Other Body`, `S5 DEC EXEMPT`, etc.) — these are excluded rather than forced into one of the four buckets, since they don't represent a completed case. 3,699 of 13,704 rows (27%) are excluded this way; **10,005 rows have a final decision.**
- **`ITMEasting`/`ITMNorthing` attribute fields are empty for all 508,657 rows in the whole dataset, not just ours** — the field is effectively dead, despite being listed in "Fields we use". The point *geometry* itself does carry real coordinates, in Web Mercator (EPSG:3857). `prep.py` fetches geometry (`returnGeometry=true`) and reprojects to Irish Transverse Mercator (EPSG:2157) with `pyproj` instead of reading the attribute. Same `itm_easting`/`itm_northing` columns as planned, just a different (working) source — **the faster-site suggestion is not blocked**, coordinate fill rate is 100% of kept rows.
- Decision split on the kept 10,005 rows: 74.8% granted, 21.9% refused, 1.9% invalid, 1.5% withdrawn.
- Fill rates on kept rows: `units` 82% (`NumResidentialUnits` plus a regex fallback from the description), `storeys` 44% (regex only — many descriptions just don't state it; LLM fallback in `tag_descriptions.py` would likely raise this but wasn't run in this check, no API key set), `decision_date`/`days_to_decision` 100%, `link` 85% (`LinkAppDetails` is null for ~15% of rows — `matching.py` should treat an empty string as "no direct link" rather than assume it's always present), `mixed_use` true for 18%, `appealed` true for 18%.
- Storeys at 44% means a reasonable share of "similar applications" won't have a storeys value — the plan's matching step already widens the band when fewer than ~20 match, which also covers rows where storeys is simply unknown.
- `invalid` and `withdrawn` rows still get a `days_to_decision`/`total_days` value (time to that administrative outcome), but it isn't a timeline for "will this be granted and how long will it take" — Role 2's aggregation likely wants `median_days_to_decision` computed over `granted`+`refused` rows only, not all four buckets, or the "typical decision in N weeks" figure will be pulled down by fast invalid/withdrawn closures.
- **Two councils don't populate `link` at all**: Dublin City Council and Dún Laoghaire–Rathdown have `link == ''` for 100% of their rows (1,246 and 304 rows respectively) — not a low fill rate, a total gap. `matching.py`/the frontend should treat empty `link` as "no direct source link" (show the reference number instead of a dead link), and the live demo shouldn't rely on clicking through for these two councils. See `data/demo_examples.md`.
- **Cork County and Cork City show exactly 0% further-information requests** (1,736 and 416 rows), and Cork County also shows 0% appeals. At that volume a genuine 0% isn't plausible — reads as `FIRequestDate`/`AppealSubmittedDate` not being populated by those two authorities in this register, not a real finding. Don't present Cork's `share_further_information`/`share_appealed` as meaningful; other councils (South Dublin, Kildare, Louth, etc.) have normal-looking rates (20–55% FI, 15–30% appealed) and are safe to use.
