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

## Known from the live source (checked 2026-10-04)

- API: `https://services.arcgis.com/NzlPQPKn5QF9v2US/arcgis/rest/services/IrishPlanningApplications/FeatureServer/0`
- 508,657 rows total; 13,704 where `DevelopmentDescription` mentions "apartment" — our filtered set.
- `maxRecordCount` is 2000 per page; pagination (`resultOffset`/`resultRecordCount`) is supported, so `prep.py` pages through all ~13.7k rows.
- `Decision` has 70+ spelling/case variants in the apartment subset alone (confirmed live, not just a guess — see the mapping in `prep.py`). A handful are not final decisions at all (`N/A`, `ADDITIONAL INFORMATION`, `Decision to be Made by Other Body`, `S5 DEC EXEMPT`, etc.) — these are excluded rather than forced into one of the four buckets, since they don't represent a completed case.
