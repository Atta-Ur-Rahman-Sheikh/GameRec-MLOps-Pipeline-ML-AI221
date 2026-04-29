# Prefect pipeline (`pipelines/`)

This folder hosts a **small Prefect 3 flow** that validates your environment:

1. Confirms the Steam CSV + RAWG JSONL paths exist (same layout as the notebook).
2. Confirms every required file exists under `artifacts/recommender/` (plus lists optional files such as clustering outputs).

It does **not** execute the training notebook automatically (that can take hours). After editing `Game_Recommender_Simple.ipynb`, run the persistence cell locally, then re-run this flow to verify the bundle before deploying the FastAPI image.

## Run

```bash
pip install -r requirements.txt   # includes prefect>=3
python -m pipelines.flow
```

With Make:

```bash
make pipeline
```

## Scheduled runs

Register the flow with your Prefect server / Cloud workspace if needed:

```bash
prefect deploy pipelines/flow.py:gamerec_artifact_pipeline \
  --name gamerec-checks \
  --cron "0 6 * * *"
```

(Exact CLI flags depend on your Prefect 3 minor version—see upstream docs.)
