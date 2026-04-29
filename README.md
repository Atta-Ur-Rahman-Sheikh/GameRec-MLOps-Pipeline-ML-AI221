# GameRec — MLOps pipeline (AI221)

End-to-end **hybrid video game recommender** with multiple ML tasks, packaged as a
production-style FastAPI service with Docker, Prefect health checks, and GitHub
Actions CI.

| Component | What it does |
|-----------|----------------|
| **Notebook** | `Game_Recommender_Simple.ipynb` — trains everything, writes `artifacts/recommender/`. |
| **API** | `app/` — FastAPI service loading artifacts at startup. |
| **Pipeline** | `pipelines/` — Prefect 3 flow validating datasets + artifact bundle. |
| **Tests** | `tests/` — pytest + `TestClient`; CI uses **tiny fixtures** under `tests/fixtures/artifacts/`. |
| **Docker** | `docker/Dockerfile` — slim Python 3.12 image; **mount** real artifacts at runtime. |
| **Report** | `report/` — IEEE two-column LaTeX skeleton (`main.tex`). |

## Quick start (local API)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt

# Point at real notebook artifacts (default: ./artifacts/recommender)
set GAMEREC_ARTIFACTS_DIR=artifacts\recommender
uvicorn app.main:app --reload --port 8000
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for Swagger UI.

### Troubleshooting installs (Windows)

- **Use Python 3.11 or 3.12** in a **fresh virtualenv** (`python -m venv .venv`). Python **3.14** is often too new: NumPy can hit **access violations** on import before tests even run.
- If `pip install` **times out**, retry or use a faster network / `pip install --retries 10`.
- **Dependency conflicts** (e.g. a globally installed `mlxtend` wanting newer NumPy than this project): prefer a clean venv with **only** `requirements-dev.txt`; avoid mixing unrelated user-site packages.

### Required artifacts

Minimum for `/health` **ok** + recommender:

- `catalog.pkl` (or `catalog.parquet`)
- `tfidf_vectorizer.joblib`, `tfidf_matrix.npz`, `svd.joblib`, `lsa_matrix.npy`, `popularity.npy`
- `player_type_classifier.joblib`, `player_types_rules.json`
- `popularity_regressor.joblib`

Optional (cluster + seasonality endpoints):

- `kmeans_clusters.joblib`, `cluster_cards.json`, `seasonality.json`

Re-run the notebook persistence cell (**Section 17**) after training to refresh all files.

## Makefile targets

```bash
make install      # pip install -r requirements-dev.txt
make api          # uvicorn with reload
make test         # pytest
make lint         # ruff check + format --check
make fixtures     # regenerate tiny CI artifacts from real ones
make docker       # docker build -f docker/Dockerfile ...
make docker-up    # docker compose up (artifacts volume-mounted)
make pipeline     # python -m pipelines.flow
```

## API surface (high level)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness + artifact status |
| `GET` | `/games/search` | Title search |
| `POST` | `/recommend/similar` | Item–item hybrid recommender |
| `POST` | `/recommend/user` | Cold-start preference recommender |
| `POST` | `/recommend/explain` | Shared tags / genres between two titles |
| `POST` | `/predict/popularity` | XGBoost cold-launch popularity (0–5 scale) |
| `POST` | `/predict/player-type/by-title` | Multi-label archetype scores (catalog game) |
| `POST` | `/predict/player-type/by-query` | Archetype scores from tags/genres only |
| `GET` | `/discover/clusters` | All KMeans cluster cards |
| `GET` | `/discover/hidden-genre/{name}` | Cluster assignment + distinctive tags |
| `GET` | `/seasonality/themes` | Themes with precomputed monthly indices |
| `GET` | `/seasonality/{theme}` | Monthly averages + seasonal index JSON |

## Docker

Build from **repo root** (context must include `app/` and `requirements.txt`):

```bash
docker build -f docker/Dockerfile -t gamerec-api:latest .
```

Run with artifacts mounted read-only:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Set `GAMEREC_ARTIFACTS_DIR=/app/artifacts/recommender` inside the container (already default in the Dockerfile).

## CI fixture artifacts

Real `tfidf_matrix.npz` + `catalog.pkl` are too large for git. CI instead uses
`tests/fixtures/artifacts/` (~few MB). Regenerate after changing training logic:

```bash
python -m tests.fixtures.build_fixtures
```

Commit the updated `tests/fixtures/artifacts/*`.

## Prefect pipeline

Validates Steam + RAWG paths exist and checks every required artifact file:

```bash
python -m pipelines.flow
```

See [pipelines/README.md](pipelines/README.md).

## Report (IEEE two-column)

```bash
cd report
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Extended ML narrative lives in `sections/*.tex`. Add figure PDFs under `figures/`.

## Project layout

```
app/              # FastAPI + services
pipelines/        # Prefect validation flow
tests/             # pytest + fixtures
docker/            # Dockerfile + compose
.github/workflows/ # CI (ruff + pytest + docker build)
report/            # LaTeX IEEE paper
artifacts/         # gitignored — produced by notebook
```

## License

See [LICENSE](LICENSE).
