# Flask ORM Repo (Flask-SQLAlchemy + Flask Test Client)

This repo teaches Flask ORM using Flask-SQLAlchemy and reuses database concepts from the previous lesson:
tables, constraints, relationships, joins, and transactions.

## Structure
- `data/` — generated SQLite DB files (ignored by git)
- `src/demo/flask_orm/` — Flask app factory + models + routes (reference solution)
- `src/demo/demo.py` — demo script that seeds in-memory data
- `src/exercises/` — in-class exercises (implement TODOs in `exercises.py`)

- `tests/` — pytest tests (functions + API routes)
- `.github/` — GitHub Classroom autograding using `education/autograding@v1`

## Setup
```bash
python -m venv .venv
source .venv/bin/activate   # mac/linux
# .venv\\Scripts\\activate  # windows
pip install -r requirements.txt
```

## Run servers / demos
- Demo reference app (uses solution code):
  ```bash
  python -m src.demo.flask_orm.run
  ```
- Exercises API (calls your implementations):
  ```bash
  python -m src.exercises.run
  ```

## What to implement
- `src/exercises/exercises.py`: all ORM functions (CRUD, queries, aggregation, updates, filtering).
- `src/homework/homework.py`: homework-gradebook helpers (assignments, grades, reports, leaderboard).

## Run tests
```bash
pytest -q tests/test_exercises.py          # function-level exercises
pytest -q tests/test_exercises_routes.py   # API routes powered by your exercises
pytest -q                                  # everything
```
