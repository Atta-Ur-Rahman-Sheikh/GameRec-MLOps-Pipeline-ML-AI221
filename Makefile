# Convenience targets for common workflows. POSIX-style; works in
# PowerShell via `make` (GnuWin) or under WSL/Git Bash. Targets match the
# names referenced in README.md and CI.

PY ?= python
PORT ?= 8000

.PHONY: help install api test lint format docker docker-up pipeline fixtures clean

help:
	@echo "Targets:"
	@echo "  install      Install runtime + dev dependencies"
	@echo "  api          Run FastAPI service locally on :$(PORT)"
	@echo "  test         Run pytest"
	@echo "  lint         Ruff lint check"
	@echo "  format       Ruff format (modifies files)"
	@echo "  docker       Build the Docker image (api:latest)"
	@echo "  docker-up    Run docker-compose up (artifacts mounted as volume)"
	@echo "  pipeline     Run the Prefect retraining flow"
	@echo "  fixtures     Build tiny CI fixture artifacts from real ones"
	@echo "  clean        Remove caches"

install:
	$(PY) -m pip install -r requirements-dev.txt

api:
	$(PY) -m uvicorn app.main:app --host 0.0.0.0 --port $(PORT) --reload

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

format:
	$(PY) -m ruff format .
	$(PY) -m ruff check --fix .

docker:
	docker build -f docker/Dockerfile -t gamerec-api:latest .

docker-up:
	docker compose -f docker/docker-compose.yml up --build

pipeline:
	$(PY) -m pipelines.flow

fixtures:
	$(PY) -m tests.fixtures.build_fixtures

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ */__pycache__ */*/__pycache__
