# <img src="./report/readme files/game-svgrepo-com (1).svg" width="30%" align="right" />Semantic Game Recommendation System with Production-Grade MLOps Infrastructure

[![Python](https://img.shields.io/badge/Python-3.13-422680?style=for-the-badge&labelColor=111827&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-341671?style=for-the-badge&labelColor=111827&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Vite-280659?style=for-the-badge&labelColor=111827&logo=react&logoColor=white)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Container-660f56?style=for-the-badge&labelColor=111827&logo=docker&logoColor=white)](https://www.docker.com/)
[![Prefect](https://img.shields.io/badge/Prefect-Orchestration-ae2d68?style=for-the-badge&labelColor=111827&logo=prefect&logoColor=white)](https://www.prefect.io/)
[![License](https://img.shields.io/badge/License-MIT-f54952?style=for-the-badge&labelColor=111827)](LICENSE)

*An end-to-end ML pipeline that turns a 79,000-game Steam + RAWG catalog into explainable, production-deployable recommendations, served via a FastAPI REST API, containerized with Docker, and guarded by a full CI/CD pipeline.*


## 👾 Project Overview
 
Game storefronts surface thousands of titles through keyword search and popularity rankings, neither of which accounts for *what a game actually feels like to play*. Two games can share identical genres but sit in completely different corners of a player's interest space.
 
This project addresses this in both modeling and engineering terms:
 
- **Semantic discovery** — TF-IDF + Latent Semantic Analysis bridges the gap between games that describe similar gameplay with different words (e.g., *sandbox* vs. *open world*), delivering recommendations that pure keyword search misses.
- **Explainability** — every recommendation surfaces the shared tags, genres, and TF-IDF features that drove the match, so results don't feel like a black box.
- **Auxiliary ML tasks** — cold-launch popularity estimation and player archetype profiling (8 playstyle labels) support richer UX and pre-release planning.
- **Production gap closure** — most student ML projects stop at a notebook. GameMind adds serialized artifacts, API contracts, fixture-based tests, lint, CI, and Docker so the system can be run and verified repeatably by anyone.

## 👾 System Architecture

<p align="center">
  <img src="report/figures/Architecture Diagram.png" alt="System Architecture Diagram" width="85%">
</p>

<p align="center">
  <em>High-level architecture of the system showing data flow and components. The notebook (`Game_Recommender_Simple.ipynb`) handles all training and exports 12 artifact files. The Prefect flow validates those artifacts exist and are structurally valid before the API starts. CI runs independently of the serving path.</em>
</p>

## 👾 ML Capabilities
 
### Hybrid Recommender
 
The core recommender scores every game against a query using a weighted blend of three signals:
 
```
score = 0.55 × cos_SVD  +  0.30 × cos_TF-IDF  +  0.15 × popularity
```
 
LSA carries the most weight to capture semantic relationships; TF-IDF preserves direct term overlap; Bayesian-smoothed popularity adds a quality prior. A second inference path accepts a list of liked games, aggregates their LSA vectors into a virtual user profile, and scores the full catalog against it (preference-driven / cold-start mode).
 
**Feature Engineering**: Each game is represented as a weighted text blob: tags (4×), genres (3×), categories (2×), description (1×). Tags receive the highest weight because they are crowd-sourced and highly specific. TF-IDF uses bigrams, sublinear TF scaling, `min_df=2`, and a 50,000-feature vocabulary cap.
 
### Explainability Module
 
For any recommended pair, the module returns overlapping genre labels, Jaccard similarity over tag sets, and the top TF-IDF feature contributions, so every recommendation comes with a human-readable "why."
 
### XGBoost Popularity Regressor
 
Predicts Bayesian-smoothed popularity from content features alone (LSA embeddings + release timing + structural metadata), simulating a cold-start pre-launch scenario.
 
### Player Archetype Classifier
 
A multi-label One-vs-Rest Logistic Regression model trained on 128-dimensional LSA embeddings predicts eight player archetypes from game metadata using weakly supervised labels (Archetypes):

<div style="display:flex; flex-wrap:wrap; gap:6px;">
  <img src="https://img.shields.io/badge/Explorer-664d00?style=for-the-badge&labelColor=111827"/>
  <img src="https://img.shields.io/badge/Narrative%20Nerd-6e2a0c?style=for-the-badge&labelColor=111827"/>
  <img src="https://img.shields.io/badge/Tinkerer-691312?style=for-the-badge&labelColor=111827"/>
  <img src="https://img.shields.io/badge/Trophy%20Hunter-5d0933?style=for-the-badge&labelColor=111827"/>
  <img src="https://img.shields.io/badge/Thrill%20Seeker-291938?style=for-the-badge&labelColor=111827"/>
  <img src="https://img.shields.io/badge/Grinder-042d3a?style=for-the-badge&labelColor=111827"/>
  <img src="https://img.shields.io/badge/Speedrunner-12403c?style=for-the-badge&labelColor=111827"/>
  <img src="https://img.shields.io/badge/Competitor-475200?style=for-the-badge&labelColor=111827"/>
</div>

### KMeans Latent Genre Discovery
 
KMeans (k=16, selected by silhouette score) clusters 79,080 games in LSA space, recovering semantically coherent latent genres e.g., *Precision Platformer*, *Boomer Shooter*, *Sokoban/Solitaire*, that official genre labels are too coarse to express.
 
### Seasonality Analysis
 
Monthly seasonal indices are computed for five themes (Horror, Strategy, RPG, Sports, Racing) across 2014–2024 release data. Horror exhibits the strongest signal, with an October peak at 1.60× its monthly average.

## 👾 Quick Start
 
### Prerequisites
 
- Python 3.11–3.13
- Node.js 18+ (frontend only)
- Docker & Docker Compose (container path only)

 
### Option 1 — Local (API + tests)
 
**1. Clone and install**
 
```bash
git clone https://github.com/<your-org>/GameRec-MLOps-Pipeline-ML-AI221.git
cd GameRec-MLOps-Pipeline-ML-AI221
 
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
 
pip install -r requirements-dev.txt
```
 
**2. Generate artifacts**
 
Open and run `Game_Recommender_Simple.ipynb` end-to-end. This produces `artifacts/recommender/` with all 12 serialized model files.
 
```bash
# Optional: validate artifacts before starting the API
python -m pipelines.flow
```
 
**3. Start the API**
 
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
 
Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — the interactive Swagger UI lets you call every endpoint directly.
 
**4. Run tests**
 
```bash
pytest tests/ -q --tb=short
```
 
Tests use fixture artifacts under `tests/fixtures/artifacts/` so the full 4 GB dataset is not required for CI.
 
 
### Option 2 — Docker Compose
 
```bash
# Artifacts must exist on the host first (run the notebook)
docker compose -f docker/docker-compose.yml up --build
```
 
The compose file mounts `../artifacts/recommender` into the container at `/app/artifacts/recommender` as a read-only bind mount. Artifacts are intentionally *not* baked into the image so the model bundle can be updated without rebuilding.
 
 
### Option 3 — Frontend (optional)
 
```bash
cd frontend
npm install
npm run dev
```
 
Set `VITE_API_BASE_URL` if the API is not on `http://127.0.0.1:8000`.

 
### Environment Variables
 
| Variable | Default | Description |
|---|---|---|
| `GAMEREC_ARTIFACTS_DIR` | `artifacts/recommender` | Path to serialized model artifacts |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | API base URL for the React frontend |
 
 
## 👾 API reference

<details>
<summary><strong>Expand endpoint table</strong></summary>

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness + artifact status |
| `GET` | `/games/search` | Title search |
| `POST` | `/recommend/similar` | Item–item hybrid recommender |
| `POST` | `/recommend/user` | Preference-based (cold-start) recs |
| `POST` | `/recommend/explain` | Shared tags/genres between titles |
| `POST` | `/predict/popularity` | XGBoost popularity (0–5 scale) |
| `POST` | `/predict/player-type/by-title` | Archetype scores (catalog game) |
| `POST` | `/predict/player-type/by-query` | Archetype scores from tags/genres |
| `GET` | `/discover/clusters` | KMeans cluster cards |
| `GET` | `/discover/hidden-genre/{name}` | Cluster + distinctive tags |
| `GET` | `/seasonality/themes` | Precomputed monthly themes |
| `GET` | `/seasonality/{theme}` | Monthly averages + seasonal index |

</details>
 
## 👾 Project Structure
<details>
<summary><strong>Expand project structure</strong></summary>
    
```
.
├── Game_Recommender_Simple.ipynb   # Training notebook — produces all artifacts
├── app/                            # FastAPI application
│   ├── main.py                     # App entry point, artifact loading
│   └── routers/                    # Route handlers per capability
├── artifacts/
│   └── recommender/                # Serialized model bundle (12 files, gitignored)
│       ├── catalog.pkl
│       ├── tfidf_vectorizer.joblib
│       ├── tfidf_matrix.npz
│       ├── svd_model.joblib
│       ├── lsa_matrix.npz
│       ├── popularity_scores.npy
│       ├── archetype_classifier.joblib
│       ├── popularity_regressor.joblib
│       ├── kmeans_clusters.joblib  
│       ├── cluster_cards.json       
│       ├── player_types_rules.json
│       └── seasonality.json        
├── pipelines/
│   └── flow.py                     # Prefect artifact validation flow
├── frontend/                       # React + Vite frontend
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/
│   ├── fixtures/
│   │   └── artifacts/              # Lightweight CI fixtures
│   └── ...
├── report/                         # IEEE LaTeX project report
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint → Test → Docker smoke build
│       └── discord-push.yml        # Discord commit notifications
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```
    
</details>

## 👾 Data & Artifacts
<details>
<summary><strong>Expand project structure</strong></summary>
    
### Datasets
 
| Source | Retained after filtering |
|---|---|
| Steam | 65,391 games |
| RAWG | 26,606 games |
| **Merged catalog** | **79,080 games** |
 
Merging uses a normalized key (`norm_key`) built from lowercase alphanumeric titles. An outer join retains games unique to either source. Popularity scores are Bayesian-smoothed across both rating systems: 
 
```
Score = (v / (v + m)) × R  +  (m / (v + m)) × C
```
 
### Artifact Files
 
The 12 serialized files in `artifacts/recommender/` are produced entirely by the training notebook and are intentionally excluded from git (they can be several GB). For CI, `tests/fixtures/build_fixtures.py` generates a lightweight stand-in:
 
```bash
python -m tests.fixtures.build_fixtures
```
 
> **Windows users:** Python 3.14 is flagged as risky in `pyproject.toml` due to scientific wheel instability. Use Python 3.11–3.13.

</details>

## 👾 Contributors

<table align="center">
  <tr>
    <td align="center">
      <a href="https://github.com/Atta-Ur-Rahman-Sheikh">
        <img src="https://github.com/Atta-Ur-Rahman-Sheikh.png" width="80px;" alt="Atta ur Rahman"/><br>
        <sub><b>Atta ur Rahman</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Bibz-a">
        <img src="https://github.com/Bibz-a.png" width="80px;" alt="Labiba Ahmad"/><br>
        <sub><b>Labiba Ahmad</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/QuratUlainAhmed">
        <img src="https://github.com/QuratUlainAhmed.png" width="80px;" alt="Qurat Ulain Ahmed"/><br>
        <sub><b>Qurat Ulain Ahmed</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/maimoonasaboorr">
        <img src="https://github.com/maimoonasaboorr.png" width="80px;" alt="Maimoona Saboor"/><br>
        <sub><b>Maimoona Saboor</b></sub>
      </a>
    </td>
  </tr>
</table>


## 👾 License
 
This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.
 
