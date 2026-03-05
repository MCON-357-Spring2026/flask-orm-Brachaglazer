# Exercises — Flask ORM Fundamentals

## What you are building
A tiny gradebook API on top of three tables:
- `Student(id, name, email)` — `email` unique
- `Assignment(id, title, max_points)` — `title` unique
- `Grade(id, score, student_id, assignment_id, created_at)` — unique `(student_id, assignment_id)`

Data model lives in `src/exercises/models.py`. Persistence uses Flask + SQLAlchemy via `src/exercises/extensions.py`.

## Your tasks
Implement **all TODOs** in `src/exercises/exercises.py`:
- Basic CRUD: create students, find by email, add grades with uniqueness/lookup checks, compute average percent per student.
- Querying: list students, fetch assignments by title, fetch grades for a student or assignment with ordering and existence checks.
- Aggregation: counts, highest score per assignment, class average percent, per-student grade counts.
- Updates/Deletes: update student email (handle duplicates), delete students (cascade grades), delete grades.
- Filtering/Analytics: students above a threshold average, assignments without grades, top scorer per assignment.

## How to run tests
Inside the repo root:
```bash
pytest -q tests/test_exercises.py            # function-level tests
pytest -q tests/test_exercises_routes.py     # API route tests that call your functions
```

## Things to watch for
- Raise `ValueError` for duplicates/validation failures as specified in docstrings.
- Raise `LookupError` when referenced students/assignments/grades do not exist.
- Use the provided session (`db.session`) and remember to rollback on integrity errors where required.
- Order query results exactly as specified (e.g., students by name, grades by assignment title or student name).
- Percent calculations: `score / max_points * 100`; return `0.0` when no grades are present.

When both test suites pass, the exercise is complete.
