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
/backend    Role 2 — FastAPI /predict endpoint
/frontend   Role 3 — screen, map, demo
CONTRACT.md, data/schema.md   shared, frozen contracts — see "Working concurrently" in the plan
```

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
