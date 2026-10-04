# Transport equity audit

A hackathon project for Build for Ireland (Dogpatch Labs, one-day build, 12:00 to 16:00).

## The idea

Public transport is meant to connect people to jobs, school and services. But the areas with the least money often have the weakest connections, and nobody can easily show it with numbers. This tool answers three questions from public data:

- Which neighbourhoods have poor transport access for how deprived they are?
- How many jobs and services can people there reach in 45 minutes without a car?
- What would one new or extended route change?

The user picks a city or county. The tool scores each small area on public transport access, compares it to deprivation and car ownership, and highlights the mismatches. A planner can then test one route change and see the before and after.

## Example

**Input:** "Where in Dublin is transport worst for the people who need it most?", then click the top result.

**Output (numbers below are made up to show the format):**

- What we found: 1,800 small areas in the Dublin region, 42 flagged as high inequity
- Top area: pop. 2,100, 38% in the most deprived band, 41% no car, 2 buses an hour in the morning peak
- Reachable by public transport in 45 minutes: 38,000 jobs, versus a region average of 210,000
- Why it scored high: low frequency, long walk to a stop, few destinations in range, high deprivation
- If the proposed route extension ran: jobs reachable rise from 38,000 to 95,000, 2,100 people affected
- A two-sentence plain-English summary
- Map layer toggles: inequity score, deprivation, stops and frequency, proposed route

## Where the data comes from

- **Timetables:** National Transport Authority GTFS static feed (Transport for Ireland). Stops, routes, trips and stop times for bus, rail, Luas and more. https://www.transportforireland.ie/transitData/PT_Data.html
- **Population, commuting and car ownership:** CSO Census 2022 Small Area Population Statistics (SAPS) and place of work data. https://data.cso.ie/
- **Small area boundaries:** Tailte Eireann / CSO boundary files.
- **Deprivation:** Pobal HP Deprivation Index (small area level), on data.gov.ie.
- **Jobs and services:** CSO place of work counts by area (POWSCAR where available), plus OSM for schools, hospitals, shops. Use job counts as the main destination measure.
- **Street network:** OpenStreetMap for walking to and from stops.
- **Licences:** NTA, CSO and Pobal are open licence. OSM is ODbL. Credit all on screen.

### Fields we use

| Need                  | Source and field                                                    |
| --------------------- | ------------------------------------------------------------------- |
| Where the service is  | GTFS `stops`, `routes`, `trips`, `stop_times`, `calendar`           |
| How often             | Trips per hour at stops in the 07:00 to 09:00 weekday window        |
| Who lives there       | SAPS total population, small area code and boundary geometry        |
| Car access            | SAPS households with no car                                         |
| Disadvantage          | Pobal HP deprivation score                                          |
| Where people work     | CSO place of work counts by area                                    |
| Walking to the stop   | OSM street network, centroid to stop distance                       |

### Known limits

- GTFS is the scheduled timetable, not real running times. We measure planned service, not delays.
- We have not confirmed fares data is open, so cost is out of scope unless we find it. The audit is about access, not price.
- Place of work data may not be at small area level. We may have to use larger zones for the jobs side. Check this first.
- Census commuting is 2022 and reflects how people travel, not how they would if service improved.
- The inequity score is a model with chosen weights. Show the weights and let the user change them.
- Door-to-door times need a routing engine. If it fights us, fall back to frequency and stops within walking distance only.
- Data is aggregated by small area. No personal data is involved, and none should be added.

## How it works

### Prep (run once, before the demo)

1. Load the GTFS feed and filter to a typical weekday morning window.
2. Load SAPS, boundaries and Pobal, and join them on small area code.
3. For each small area, compute walking distance to the nearest stops and trips per hour at those stops.
4. Compute jobs reachable in 45 minutes by public transport (a routing engine such as r5py or OpenTripPlanner, or a simpler stop-to-stop approximation).
5. Compute the inequity score: need (deprived, no car) against access (frequency, jobs reachable).
6. Save one table (GeoParquet or SQLite plus GeoJSON) and keep a local copy.

### Live (per query)

1. **Select:** the user picks a city or county. The model can also turn a sentence ("estates on the edge of Cork with no car") into filters.
2. **Rank:** a SQL query returns small areas sorted by inequity score with the weights shown.
3. **Simulate:** the user adds or extends one route. Recompute access for areas near it and show jobs reachable before and after.
4. **Explain:** the model writes a short summary using only the computed numbers, so it cannot invent figures.
5. **Display:** map, ranked list, area detail card, before and after for the proposed route.

## The three roles

### Role 1: data

Owns the prep pipeline. This is the critical path, so it starts first.

- Load GTFS, SAPS, boundaries, Pobal, check coverage
- Join everything on small area code
- Compute frequency, jobs reachable and the inequity score
- Sanity check against a few areas we know well
- Pick three demo areas that tell a clear story

### Role 2: model and backend

Owns the scoring logic, the simulation and the single endpoint the front end calls.

- Endpoint for ranked areas and area detail
- Route change simulation (recompute access near a drawn route)
- Natural language to filter prompt and JSON schema
- Summary prompt that uses only computed numbers
- Fallback to frequency only if routing is too slow

### Role 3: front end and demo

Owns the screen and the presentation.

- Build the map and ranked list against mock JSON, then connect to the real endpoint
- Weight sliders for the inequity score, route drawing for the simulation
- Area detail card with the before and after
- Record a backup video of the working demo
- Rehearse and deliver the pitch

## Schedule

| Time           | Role 1: data                              | Role 2: model and backend        | Role 3: front end and demo      |
| -------------- | ----------------------------------------- | -------------------------------- | ------------------------------- |
| 12:00 to 12:30 | Load GTFS, SAPS, boundaries, Pobal        | Endpoint shape and mock JSON     | Map shell against mock JSON     |
| 12:30 to 13:00 | Join data, compute stop frequency         | Ranking query                    | Ranked list and area card       |
| 13:00 to 13:30 | Lunch (reachability job running)          | Lunch                            | Lunch                           |
| 13:30 to 14:30 | Finish jobs reachable, inequity score     | Route change simulation          | Weight sliders and route draw   |
| 14:30 to 15:15 | Sanity check scores, pick demo areas      | Filter and summary prompts       | Connect to the real endpoint    |
| 15:15 to 15:45 | Final data export                         | Bug fixes and fallbacks          | Polish, record backup video     |
| 15:45 to 16:00 | Submit                                    | Submit                           | Rehearse the pitch              |

**Go or no-go at 12:30.** If the jobs data or routing is not working, drop reachability and rank on frequency, walk distance to a stop and deprivation. Still a complete demo.

## Build order

1. Map of small areas coloured by inequity score
2. Ranked list with a "why" breakdown per area
3. Route change simulation with jobs reachable before and after
4. Chat box over the results (if time allows)
5. Add real-time reliability from the NTA realtime feed (stretch goal only)

Steps 1 to 3 are one pipeline and make a complete demo on their own.

## Presenting it

- Show the population behind every figure, and warn when an area is small.
- Be clear this measures scheduled service and access, not delays or fares.
- Show the score weights on screen. Frame it as "where to look first", not "proof of policy failure".
- In the demo, pick one area, show why it scored badly, then draw a route and show jobs reachable change.
- Only quote numbers the tool actually produced.
- Keep the processed data local and have the backup video ready in case the wifi fails.

## Before the day

- Download the GTFS feed, SAPS, boundaries and Pobal data, and check column names.
- Decide the region (Dublin or one city is plenty) and the three demo areas.
- Check whether place of work data exists at small area level, and pick the fallback if not.
- Test a routing library on a small sample if we plan to use one.
- Confirm everyone has their OpenAI credits and API access working.
- Agree the JSON shape that the endpoint returns, so the front end can start against mock data.
