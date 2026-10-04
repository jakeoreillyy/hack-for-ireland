# hack-for-ireland

## Planning permission predictor

Build for Ireland hackathon project (Dogpatch Labs, one-day build). Describe a
proposed apartment development and a council, and see how similar past
applications in the national planning register actually went — grant rate,
typical time to decision, and what tends to add delay (further information
requests, appeals) — with links to the real cases.

- [Full plan](planning-predictor-plan.md) — idea, data sources, schedule, build order
- [API contract](CONTRACT.md) — the frozen `POST /predict` request/response shape
- [Data schema](data/schema.md) — the table `data/prep.py` produces, plus real fill-rate findings and known limits
- [Demo examples](data/demo_examples.md) — 3 verified examples with real stats and working links to rehearse with

An earlier alternative direction is proposed in
[TRANSFORMATION_PLAN.md](TRANSFORMATION_PLAN.md) (reusing an existing
"RentCheck" app on a different stack). The team is building the planning
predictor above.

### Repo layout

```
/data       Role 1 — data pipeline (done, see below)
/apps/backend   Role 2 — FastAPI /predict endpoint (see "Backend" below)
/apps/frontend  Role 3 — screen, map, demo
CONTRACT.md, data/schema.md   shared, frozen contracts — see "Working concurrently" in the plan
```

### Run everything

```bash
# 1. data (once): writes data/applications.parquet, ~30 s, needs internet
pip install -r data/requirements.txt && python data/prep.py

# 2. API, http://127.0.0.1:8000 (optional: add ANTHROPIC_API_KEY to apps/backend/.env)
cd apps/backend && pip install -e ".[dev]" && uvicorn planning_predictor.main:app --reload

# 3. app, http://localhost:3000 (second terminal)
cd apps/frontend && npm install && npm run dev
```

Without step 1 the API falls back to `data/fake_sample.csv` (10 rows). For the live demo, type
"100 apartments" with Dublin City Council, then tap the map to drop a site.

### Data pipeline (Role 1 — ready to build on)

```bash
python3 -m venv /tmp/hfi-venv && source /tmp/hfi-venv/bin/activate   # keep the venv outside this OneDrive-synced folder
pip install -r data/requirements.txt

python3 data/prep.py                   # fetches the live register, writes data/applications.parquet (~10,000 rows)
python3 data/test_pipeline.py          # fast unit tests, no network
python3 data/verify_demo_examples.py   # confirms demo_examples.md numbers + links still hold
```

`applications.parquet`/`.csv` are gitignored (regenerate with `prep.py`,
takes ~20–30s). `data/fake_sample.csv` has the same columns for testing
before the real file exists.

## Backend (`apps/backend`)

FastAPI service exposing `POST /predict` and `GET /health`.

```bash
cd apps/backend
cp .env.example .env
pip install -e ".[dev]"
uvicorn planning_predictor.main:app --reload
pytest && ruff check .
```

- Settings come from `apps/backend/.env` and environment variables; every tunable is in `config.py`. Tests ignore `.env`, so they never call the real API.
- Claude is optional: with no `ANTHROPIC_API_KEY` the description is read by regex only. A form can skip parsing by sending `parsed_override`.
- `python scripts/check_parsing.py` scores the description parser on sample descriptions; add `--llm` to include Claude (calls the API with your key).
- Data is read from `data/applications.parquet`, falling back to `data/fake_sample.csv`. The server refuses to start if neither exists or a required column is missing.
