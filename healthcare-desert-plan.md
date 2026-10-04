# Healthcare desert finder

A hackathon project for Build for Ireland (Dogpatch Labs, one-day build, 12:00 to 16:00).

## The idea

Some parts of Ireland have lots of older people and very few GPs within reach. Nobody planning health services can easily see where the gap is biggest. This tool answers three questions from public data:

- Which areas have the worst GP access for the people who need it most?
- How far is the nearest GP, and how many people share each one?
- If a new GP practice opened here, how many people would it help?

The user picks a county or council area. The tool ranks small areas by a transparent "gap score", draws them on a map, and lets a planner click an area to see why it scored badly and what a new practice would change.

## Example

**Input:** "Show me the worst-served areas in Co. Mayo", then click the top result.

**Output (numbers below are made up to show the format):**

- What we found: 214 small areas in Mayo, 18 flagged as high gap
- Top area: pop. 1,240, 31% aged 65+, nearest GP 14 km (22 min drive), 1 GP within 20 min per 2,900 people
- Why it scored high: older than county average, no practice within 15 min, low car ownership
- If a practice opened at the marked site: 3,100 people move inside 15 min, 940 of them aged 65+
- A two-sentence plain-English summary
- Map layer toggles: all GPs, high-gap areas, the proposed site

## Where the data comes from

- **Population and age:** CSO Census 2022 Small Area Population Statistics (SAPS). Age bands, general health, disability, carers, car ownership by small area. https://data.cso.ie/ and https://www.cso.ie/en/census/census2022/
- **Small area boundaries:** Tailte Eireann / CSO boundary files (GeoJSON or shapefile). Needed to draw the map.
- **GP locations:** OpenStreetMap, `amenity=doctors` and `healthcare=doctor` via the Overpass API. HSE and ICGP practice lists are a possible cross-check.
- **Deprivation:** Pobal HP Deprivation Index (small area level), on data.gov.ie.
- **Travel times:** OpenStreetMap road network, routed locally (OSRM or openrouteservice) or approximated with a distance buffer.
- **Licences:** CSO and Pobal are open licence. OSM is ODbL. Credit all three on screen.

### Fields we use

| Need                | Source and field                                                         |
| ------------------- | ------------------------------------------------------------------------ |
| Who lives there     | SAPS total population and age bands, especially 65+ and 75+              |
| How healthy         | SAPS "general health" bad or very bad, disability, carers                |
| Mobility            | SAPS households with no car                                              |
| Where they live     | Small area code and boundary geometry                                    |
| Where GPs are       | OSM doctor nodes and polygons (lat, lon, name)                           |
| Disadvantage        | Pobal HP deprivation score                                               |
| Drive time          | Routed minutes from small area centroid to nearest GP                    |

### Known limits

- OSM GP coverage is not guaranteed complete. Practices can be missing or mislabelled. This is the first thing to check.
- There is no public count of GPs per practice or open GMS panels, so we measure practices, not doctor capacity. Say so on screen.
- We have confirmed the sources exist but not that every field is filled consistently. Check SAPS table and column names on load.
- Census data is from 2022. Population has moved since, and we cannot show waiting times or appointment availability.
- The gap score is a model with chosen weights, not a measured outcome. Show the weights and let the user change them.
- Small areas are public and aggregated. No personal data is involved, and none should be added.

## How it works

### Prep (run once, before the demo)

1. Load SAPS and the small area boundaries. Keep population, age, health, car ownership.
2. Pull GP locations from OSM for the chosen region. Deduplicate and clean names.
3. Join the Pobal deprivation score to each small area.
4. Compute drive time from each small area centroid to the nearest GP, and the count of GPs within 15 and 30 minutes.
5. Compute the gap score per area: need (older, unwell, low car access, deprived) divided by access (distance and practices per head).
6. Save one table (GeoParquet or SQLite plus GeoJSON) and keep a local copy.

### Live (per query)

1. **Select:** the user picks a county or council area. The model can also turn a sentence ("rural areas in the west with lots of over-75s") into filters.
2. **Rank:** a SQL query returns small areas sorted by gap score with the weights shown.
3. **Simulate:** the user drops a pin for a proposed practice. Recompute drive times and population moved inside 15 minutes.
4. **Explain:** the model writes a short summary using only the computed numbers, so it cannot invent figures.
5. **Display:** map, ranked list, area detail card, before and after for the proposed site.

## The three roles

### Role 1: data

Owns the prep pipeline. This is the critical path, so it starts first.

- Load SAPS, boundaries, Pobal and OSM GP data, check coverage
- Join everything on small area code
- Compute drive times and the gap score
- Sanity check against a few areas we know well
- Pick three demo areas that tell a clear story

### Role 2: model and backend

Owns the scoring logic, the simulation and the single endpoint the front end calls.

- Endpoint for ranked areas and area detail
- "New practice" simulation (recompute access for areas near a pin)
- Natural language to filter prompt and JSON schema
- Summary prompt that uses only computed numbers
- Fallback when a region has few GPs in OSM

### Role 3: front end and demo

Owns the screen and the presentation.

- Build the map and ranked list against mock JSON, then connect to the real endpoint
- Weight sliders for the gap score, pin drop for a new practice
- Area detail card with the before and after
- Record a backup video of the working demo
- Rehearse and deliver the pitch

## Schedule

| Time           | Role 1: data                              | Role 2: model and backend        | Role 3: front end and demo      |
| -------------- | ----------------------------------------- | -------------------------------- | ------------------------------- |
| 12:00 to 12:30 | Load SAPS and boundaries, pull OSM GPs    | Endpoint shape and mock JSON     | Map shell against mock JSON     |
| 12:30 to 13:00 | Join data, check GP coverage              | Ranking query                    | Ranked list and area card       |
| 13:00 to 13:30 | Lunch (drive time job running)            | Lunch                            | Lunch                           |
| 13:30 to 14:30 | Finish drive times, gap score             | New practice simulation          | Weight sliders and pin drop     |
| 14:30 to 15:15 | Sanity check scores, pick demo areas      | Filter and summary prompts       | Connect to the real endpoint    |
| 15:15 to 15:45 | Final data export                         | Bug fixes and fallbacks          | Polish, record backup video     |
| 15:45 to 16:00 | Submit                                    | Submit                           | Rehearse the pitch              |

**Go or no-go at 12:30.** If OSM GP coverage is poor, narrow to one county where we can verify it, or use straight-line distance instead of routed drive time.

## Build order

1. Map of small areas coloured by gap score
2. Ranked list with a "why" breakdown per area
3. New practice simulation with people helped
4. Chat box over the results (if time allows)
5. Compare against HSE or ICGP practice lists (stretch goal only)

Steps 1 to 3 are one pipeline and make a complete demo on their own.

## Presenting it

- Show the population behind every figure, and warn when an area is small.
- Be clear this measures practices and distance, not appointment waiting times.
- Show the score weights on screen. Frame it as "where to look first", not "where the problem is proven".
- In the demo, pick one area, show why it scored badly, then drop a pin and show people helped.
- Only quote numbers the tool actually produced.
- Keep the processed data local and have the backup video ready in case the wifi fails.

## Before the day

- Download SAPS, boundaries and Pobal data, and check column names.
- Pull OSM GPs for the target region and spot check ten against Google Maps.
- Decide the region (one county is plenty) and the three demo areas.
- Confirm everyone has their OpenAI credits and API access working.
- Agree the JSON shape that the endpoint returns, so the front end can start against mock data.
