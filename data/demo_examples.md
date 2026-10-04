# Demo examples

Three examples picked from `applications.parquet` (10,005 real rows), chosen with
`pick_demo_examples.py`. Every number below is computed directly from the real
table — nothing here is made up. These also work as known-correct test cases:
if Role 2's `matching.py` doesn't reproduce these stats for the same inputs,
something in the matching/aggregation logic disagrees with this reference.

**Why these three and not others:** picked for (a) a large enough sample to not
be dominated by a "small sample" warning, (b) a clean, honest story, and
(c) councils where the data is actually reliable — see "Data gaps that ruled
out other councils" at the bottom before picking a different one.

---

## 1. The confident one — big scheme, fast, mostly granted

**Type this live:** "150 apartments in a 10-storey block in Citywest, South Dublin"
**Council:** South Dublin County Council

```json
"parsed": { "units": 150, "storeys": 10, "mixed_use": false, "council": "South Dublin County Council" },
"stats": {
  "n_similar": 84,
  "n_decided": 78,
  "grant_rate": 0.83,
  "median_days_to_decision": 51,
  "share_further_information": 0.45,
  "share_appealed": 0.31
},
"delay_factors": [
  { "factor": "appeal", "added_days": 112 }
]
```

No further-information figure shown here on purpose — in this band it came out
*negative* (FI cases were ~4 weeks faster, on 45%+ of a 78-row sample), which is
counterintuitive and not something to present as a finding without digging into
why. `pick_demo_examples.py` only reports an effect when both sides of the
comparison have 5+ cases; this one cleared that bar but still isn't a sensible
number to put in a plain-English summary, so leave it out rather than word
around it.

**Summary (template, no model needed):** "Similar 150-unit, 10-storey schemes in
South Dublin were granted permission 83% of the time, with a typical decision
in about 7 weeks. Cases that went to appeal took about 16 weeks longer."

**Closest matches (real, clickable):**
| id | units | storeys | decision | date | link |
| --- | --- | --- | --- | --- | --- |
| SHD3ABP-312430-22 | 144 | 9 | granted | 2022-06-27 | https://planning.agileapplications.ie/southdublin/application-details/61773 |
| SD26A/0184W | 99 | 10 | refused | 2026-09-21 | https://planning.agileapplications.ie/southdublin/application-details/70736 |
| SDZ21A/0007 | 185 | 9 | granted | 2021-09-13 | https://planning.agileapplications.ie/southdublin/application-details/60624 |

---

## 2. The delay-factor showcase — smaller sample, dramatic, honest about it

**Type this live:** "90 apartments in a 6-storey development near Naas, with ground-floor retail"
**Council:** Kildare County Council

```json
"parsed": { "units": 90, "storeys": 6, "mixed_use": true, "council": "Kildare County Council" },
"stats": {
  "n_similar": 20,
  "n_decided": 20,
  "grant_rate": 0.75,
  "median_days_to_decision": 227,
  "share_further_information": 0.65,
  "share_appealed": 0.40
},
"delay_factors": [
  { "factor": "further_information_request", "added_days": 224 },
  { "factor": "appeal", "added_days": 336 }
],
"warnings": ["Only 20 similar applications found in Kildare for this size — treat the timing figures as indicative."]
```

This is the best moment to demonstrate the small-sample warning from
`CONTRACT.md` — n=20 is right at the threshold, the numbers are dramatic (32
weeks typical, nearly a year with an appeal), and that's exactly the case
where showing the warning next to the numbers matters most for credibility.

**Summary:** "Similar 90-unit, 6-storey schemes in Kildare were granted 75% of
the time, but typically took about 32 weeks to decide, based on a smaller
sample of 20 cases. A further information request added about 32 weeks, and
an appeal added about 48 weeks."

**Closest matches (real, clickable):**
| id | units | storeys | decision | date | link |
| --- | --- | --- | --- | --- | --- |
| 211606 | 55 | 5 | granted | 2022-08-05 | http://www.eplanning.ie/KildareCC/AppFileRefDetails/211606/0 |
| 2560988 | 76 | 4 | granted | 2025-10-23 | http://www.eplanning.ie/KildareCC/AppFileRefDetails/2560988/0 |
| 18301818 | 112 | 4 | granted | 2018-09-24 | http://www.eplanning.ie/KildareCC/AppFileRefDetails/18301818/0 |

---

## 3. The regional one — different geography, clean numbers, no drama

**Type this live:** "60 apartments in a 5-storey scheme in Drogheda, Co. Louth"
**Council:** Louth County Council

```json
"parsed": { "units": 60, "storeys": 5, "mixed_use": false, "council": "Louth County Council" },
"stats": {
  "n_similar": 31,
  "n_decided": 31,
  "grant_rate": 0.81,
  "median_days_to_decision": 161,
  "share_further_information": 0.65,
  "share_appealed": 0.42
},
"delay_factors": [
  { "factor": "further_information_request", "added_days": 154 },
  { "factor": "appeal", "added_days": 245 }
]
```

**Summary:** "Similar 60-unit, 5-storey schemes in Louth were granted 81% of
the time, with a typical decision in about 23 weeks. A further information
request added about 22 weeks, and an appeal added about 35 weeks."

**Closest matches (real, clickable):**
| id | units | storeys | decision | date | link |
| --- | --- | --- | --- | --- | --- |
| 201086 | 57 | 5 | granted | 2021-06-24 | http://www.eplanning.ie/LouthCC/AppFileRefDetails/201086/0 |
| 211344 | 60 | 4 | granted | 2022-05-26 | http://www.eplanning.ie/LouthCC/AppFileRefDetails/211344/0 |
| 2360494 | 68 | 4 | granted | 2024-04-19 | http://www.eplanning.ie/LouthCC/AppFileRefDetails/2360494/0 |

---

## Data gaps that ruled out other councils

Found while picking these — worth knowing before swapping in a different example:

- **Dublin City Council and Dún Laoghaire–Rathdown have 0% link fill** (`LinkAppDetails` is null for every row — 1,246 and 304 rows respectively). Despite DCC being the council in the plan's own worked example, **don't use it for the live "click through to a real application" demo moment** — there's nothing to click through to. Everything else about DCC's data is fine (56% storeys fill, normal FI/appeal rates), so it's still usable for the typed-example stats, just not the link click.
- **Cork County and Cork City show exactly 0% further-information requests** (1,736 and 416 rows) and Cork County also shows 0% appeals — at that volume, a real 0% is not plausible, so this reads as a field the Cork authorities don't populate in the national register, not a real finding. Avoid presenting Cork's `share_further_information`/`share_appealed` as if they mean "Cork never asks for more information" — don't use Cork for the delay-factor demo moment.
