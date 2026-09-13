# Samvahak — Backend Complete (Phases 1 + 2)

*"Connecting Every Village. Predicting Every Disruption."*

The **entire backend** is now built and wired together: database, auth/RBAC,
every REST API group from the spec, the AI prediction engine, and a
WebSocket channel for live updates. The Next.js frontend (dashboard, map,
i18n, offline reporting) is the next phase.

## What's working right now

- FastAPI app (`backend/app/main.py`) with CORS, global error handling, health check
- Full SQLAlchemy schema for all 11 core models (`backend/app/models/`), including
  PostGIS `Geometry` columns on `Road`/`Route` for future GIS queries
- Alembic migrations wired up (`backend/alembic/`)
- JWT auth + bcrypt password hashing + role-based access control (`backend/app/core/`)
- Realistic seed data: all 8 NER states, 24 real districts, 6 real routes,
  3 vehicles, 3 shipments, 3 incidents, weather + notifications, and one demo
  login per role
- **AI prediction engine** (`backend/app/ai/prediction.py`) — deterministic,
  explainable risk scoring: route risk (weather + incidents + landslide
  history + route status), safest/fastest/alternate route generation, and
  shipment priority-escalation recommendations. Every score comes with a
  plain-language `factors` list — no unexplained numbers.
- **Every REST API group from the spec, fully implemented:**
  - `POST /api/auth/register`, `/login`, `GET /me`
  - `GET/PATCH /api/users` — admin user management + RBAC changes
  - `GET /api/states`, `/api/states/{id}/districts`, `/api/districts`, `/api/roads`
  - `GET /api/routes`, `GET /api/routes/{id}`, `GET /api/routes/{id}/risk` (live AI score)
  - `POST /api/route-intelligence` — safest/fastest/alternate for any source→destination
  - `GET /api/vehicles`, `PATCH /api/vehicles/{id}/location`
  - `GET/POST /api/shipments`, `PATCH /api/shipments/{id}/status`,
    `GET /api/shipments/{id}/priority-recommendation` (AI escalation check)
  - `GET/POST /api/incidents`, `PATCH /api/incidents/{id}/status`
  - `GET/POST /api/citizen-reports`, `POST /api/citizen-reports/sync` (offline
    batch sync, idempotent by client-generated UUID), `GET /track/{client_uuid}`
  - `GET/POST /api/weather`, `GET/PATCH /api/notifications`
  - `GET /api/dashboard/stats` — single aggregate call for the Command Dashboard's KPI cards
  - `WS /api/ws` — live broadcast channel: vehicle/shipment/incident/report/weather updates

## Local setup (Docker — recommended)

```bash
cd samvahak
cp backend/.env.example backend/.env
# edit backend/.env — at minimum set a real JWT_SECRET_KEY

docker compose up --build
```

This starts Postgres/PostGIS on `localhost:5432` and the API on
`localhost:8000`. First time only, run migrations and seed data:

```bash
docker compose exec backend alembic revision --autogenerate -m "initial schema"
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed
```

Check it's alive: `curl http://localhost:8000/api/health`
Interactive API docs: `http://localhost:8000/docs`

## Local setup (without Docker)

```bash
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then point DATABASE_URL at your own local Postgres/PostGIS

alembic revision --autogenerate -m "initial schema"
alembic upgrade head
python -m app.db.seed

uvicorn app.main:app --reload
```

## Demo login credentials (seeded)

| Role | Email | Password |
|---|---|---|
| Admin | admin@samvahak.gov.in | Admin@123 |
| Government Officer | officer@samvahak.gov.in | Officer@123 |
| Field Staff | field@samvahak.gov.in | Field@123 |
| Citizen | citizen@samvahak.gov.in | Citizen@123 |

Log in via `POST /api/auth/login` with `{"email": "...", "password": "..."}`
— you get back a JWT to use as `Authorization: Bearer <token>` on protected
routes.

## Deploying the backend live (Railway)

1. Push this repo to GitHub.
2. In Railway: **New Project → Deploy from GitHub repo**, pick `backend/` as
   the root.
3. **Add a PostgreSQL plugin** to the project — check that PostGIS is
   enabled (Railway's Postgres template supports it; if using plain
   Postgres, connect once and run `CREATE EXTENSION postgis;`).
4. Railway auto-injects `DATABASE_URL` — no need to set it manually.
5. Set `JWT_SECRET_KEY` and `CORS_ORIGINS` (your Vercel frontend URL) in
   Railway's environment variables.
6. Railway builds from the `Dockerfile` automatically. Once deployed, run
   the migration + seed commands via Railway's shell (`railway run alembic
   upgrade head`, then `railway run python -m app.db.seed`).

## Environment variables (backend/.env)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string (auto-set by Railway in prod) |
| `JWT_SECRET_KEY` | Secret for signing auth tokens — **must** be changed for production |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime, default 1440 (24h) |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |
| `ENVIRONMENT` | `development` / `production` |

## Project structure so far

```
samvahak/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── script.py.mako
│   └── app/
│       ├── main.py
│       ├── core/          # config, security, RBAC deps
│       ├── db/            # session, seed script
│       ├── models/        # SQLAlchemy models (11 tables)
│       ├── schemas/       # Pydantic request/response models
│       ├── routers/       # auth, users, geo, logistics, incidents,
│       │                  # citizen_reports, operations (weather/notifications/
│       │                  # dashboard), ws (WebSocket)
│       ├── services/      # ws_manager (broadcast connection manager)
│       └── ai/            # prediction.py — the AI engine
└── frontend/               # Next.js app (next phase)
```

## Coming in Phase 3+

- Next.js + TypeScript frontend, dashboard-centric layout (map ≈55–65% of viewport)
- Leaflet GIS map, Recharts analytics, shadcn/ui components
- i18n (10 languages)
- Offline-first citizen reporting with sync queue
- Vercel deployment
