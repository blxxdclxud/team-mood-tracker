# Team Mood Tracker

A lightweight internal tool for agile teams to monitor collective well-being.
Submit daily mood entries, explore historical trends, and view team-wide distributions via a Streamlit dashboard backed by a FastAPI REST API.

## Requirements

- Python 3.12+
- [Poetry](https://python-poetry.org/)

## Installation

```bash
git clone <repository-url>
cd team-mood-tracker
poetry install
poetry run pre-commit install
```

## Running

Start the backend and frontend in separate terminals:

```bash
# Backend
poetry run uvicorn src.main:app --reload

# Frontend
poetry run streamlit run frontend/app.py
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## Project Structure

```
src/
    main.py             # FastAPI application entry point
    database.py         # SQLAlchemy engine and session management
    models.py           # ORM models and Pydantic schemas
    crud.py             # Database operations and analytics logic
    routes/
        moods.py        # CRUD endpoints /moods
        stats.py        # Analytics endpoints /stats
frontend/
    app.py              # Streamlit dashboard
tests/
    conftest.py         # Fixtures: transactional test DB, TestClient
    test_moods.py       # CRUD endpoint tests
    test_stats.py       # Analytics endpoint tests
locustfile.py           # Load test script
.github/workflows/
    ci.yml              # GitHub Actions CI pipeline
```

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/moods/` | Submit a mood entry |
| GET | `/moods/` | List entries (filters: user, mood, date range, pagination) |
| GET | `/moods/{id}` | Get a single entry |
| PUT | `/moods/{id}` | Update mood and/or comment |
| DELETE | `/moods/{id}` | Delete an entry |
| GET | `/stats/daily` | Average rating per day for the last N days |
| GET | `/stats/aggregate` | Aggregate stats for a date range |
| GET | `/stats/distribution` | Mood distribution counts (by day or all-time) |
| GET | `/health` | Health check |

Mood values: `excited` (5), `happy` (4), `neutral` (3), `sad` (2), `stressed` (1). Rating is derived automatically from the mood field.

## Testing

```bash
# Run tests with coverage report
poetry run pytest tests/

# Run without coverage
poetry run pytest tests/ --no-cov
```

Coverage: 97% (threshold: 80%).

## Quality Checks

All tools are configured in `pyproject.toml`.

```bash
poetry run black --check src/          # Formatting
poetry run ruff check src/             # Linting
poetry run mypy src/                   # Type checking
poetry run bandit -r src/ -lll         # Security (code)
poetry run pip-audit --ignore-vuln PYSEC-2022-42969  # Security (deps)
poetry run interrogate src/            # Docstring coverage
poetry run radon cc -a -s src/         # Cyclomatic complexity
```

| Check | Tool | Threshold | Result |
|---|---|---|---|
| Formatting | black | 100% | pass |
| Linting | ruff | 0 errors | pass |
| Type checking | mypy | 0 errors | pass |
| Security (code) | bandit | 0 high-severity | pass |
| Security (deps) | pip-audit | 0 vulnerabilities | pass |
| Docstrings | interrogate | 100% | 42/42 |
| Complexity | radon | < 5 per function | max 4 |
| Coverage | pytest-cov | >= 80% | 97% |
| Unit tests | pytest | 100% pass | 38/38 |
| API response time P95 | locust | < 150ms | 10ms |

> `py` 1.11.0 (PYSEC-2022-42969) is a transitive dependency of `interrogate` with no published fix.
> It is ignored in pip-audit as it only affects Windows path handling and does not impact this codebase.

## CI / CD

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs on every pull request and push to `main`:

```
black -> ruff -> mypy -> bandit -> pip-audit -> interrogate -> radon -> pytest + coverage
```

Pre-commit hooks (`.pre-commit-config.yaml`) block `git push` on `flake8` or `bandit` errors.

**Quality gates:**

| Gate | When | Blocks on |
|---|---|---|
| Pre-commit | Before push | flake8 or bandit errors |
| PR | On PR create / update | Failed tests, mypy errors, coverage < 80%, self-review |
| Release | Before demo | Any of features 1-6 missing, CI failure |

## Load Testing

Not a CI gate. Run manually against a live server:

```bash
locust -f locustfile.py --headless -u 10 -r 1 -t 1m
```

## Team Responsibilities

| Member | Area | Files |
|---|---|---|
| 1 - Backend Core | Models, database, CRUD logic | `src/models.py`, `src/database.py`, `src/crud.py`, `src/__init__.py` |
| 2 - Backend API | Routes, OpenAPI documentation, app entry point | `src/routes/`, `src/main.py` |
| 3 - Frontend + Load | Streamlit dashboard, load tests | `frontend/`, `locustfile.py` |
| 4 - Tests + DevOps | Unit tests, CI pipeline, quality config | `tests/`, `.github/`, `.pre-commit-config.yaml`, `pyproject.toml` |

Member 1 should start first as all other members depend on the models and CRUD layer.
