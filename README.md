# SONAE — FastAPI + Jinja + PostgreSQL

This is a server-rendered rewrite of the provided React prototype.

## Structure

- `app/main.py` — FastAPI routes and form actions
- `app/models.py` — SQLAlchemy ORM models
- `app/database.py` — database connection/session
- `app/services.py` — capacity, fill, alert calculations
- `app/seed.py` — demo data matching the prototype
- `app/templates/` — Jinja templates
- `app/static/css/styles.css` — responsive stylesheet
- `app/static/js/app.js` — small progressive-enhancement JS only
- `db/schema.sql` — PostgreSQL DDL

## Run locally with SQLite

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## PostgreSQL

Create a database/user, then set:

```bash
export DATABASE_URL='postgresql+psycopg://sonae:password@localhost:5432/sonae'
export SECRET_KEY='replace-with-a-random-secret'
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You can alternatively execute `db/schema.sql` yourself before starting the app. SQLAlchemy also calls `create_all()` for missing tables.

## Demo credentials

- Building PINs: `1001`, `2002`, `3003`, `4004`
- City user: `admin` / `sonae2026`

These are demo credentials only. Replace them before deployment.

## Production notes

- Put the app behind HTTPS and set secure session-cookie settings.
- Replace demo authentication with your real IdP/Keycloak flow if this is going into the CAMA-style environment.
- Add CSRF protection before treating POST forms as production-ready.
- Add Alembic migrations instead of relying on `create_all()` after the schema starts evolving.
