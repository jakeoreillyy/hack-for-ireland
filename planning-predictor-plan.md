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
4. **Explain:** the model writes a short summary using only the computed numbers, so it cannot invent figures.
5. **Display:** parsed details, stats, delay factors, summary, closest matches.

## The three roles

### Role 1: data

Owns the prep pipeline. This is the critical path, so it starts first.

- Load and filter the register, check fill rates
- Normalise decisions and compute timings
- Run the tagging job
- Produce the delay factor numbers
- Pick three demo examples that return good results

### Role 2: model and backend

Owns the prompts and the single endpoint the front end calls.

- Parsing prompt and JSON schema, tested on real descriptions
- Matching query and aggregation
- Summary prompt that uses only computed numbers
- Fallback behaviour when few applications match

### Role 3: front end and demo

Owns the screen and the presentation.

- Build the single screen against mock JSON, then connect to the real endpoint
- Input form, stats cards, delay factors, closest matches with links
- Record a backup video of the working demo
- Rehearse and deliver the pitch

## Schedule

| Time           | Role 1: data                         | Role 2: model and backend         | Role 3: front end and demo   |
| -------------- | ------------------------------------ | --------------------------------- | ---------------------------- |
| 12:00 to 12:30 | Load, filter, check fill rates       | Parsing prompt and schema         | Screen against mock JSON     |
| 12:30 to 13:00 | Normalise decisions, compute timings | Test parsing on 20 descriptions   | Input form and stats cards   |
| 13:00 to 13:30 | Lunch (tagging job running)          | Lunch                             | Lunch                        |
| 13:30 to 14:30 | Finish tagging, save the table       | Matching and aggregation endpoint | Closest matches list         |
| 14:30 to 15:15 | Delay factor numbers                 | Summary prompt                    | Connect to the real endpoint |
| 15:15 to 15:45 | Choose demo examples                 | Bug fixes and fallbacks           | Polish, record backup video  |
| 15:45 to 16:00 | Submit                               | Submit                            | Rehearse the pitch           |

**Go or no-go at 12:30.** If fill rates are poor, narrow to Dublin's four councils or match on units only and drop storeys.

## Build order

1. Similar applications and grant rate
2. Predicted time to decision
3. Delay factors with days lost
4. Chat box over the results (if time allows)
5. Compliance check against the 2025 apartment standards (stretch goal only)

Steps 1 to 3 are one pipeline and make a complete demo on their own.

## Presenting it

- Show the number of similar applications behind every figure, and warn when it is small.
- Word the delay figures as comparisons ("similar applications without a further information request were decided N weeks faster"), not as proof of cause.
- In the demo, type a tested example live, then click through to one real application on the council's site.
- Only quote numbers the tool actually produced.
- Keep the processed data local and have the backup video ready in case the wifi fails.

## Before the day

- Download the data and check fill rates for apartment rows (decision, both dates, unit count).
- Confirm everyone has their OpenAI credits and API access working.
- Agree the JSON shape that the endpoint returns, so the front end can start against mock data.
