# Plan Big

**Dream Big. Plan Bigger.**

Plan Big is a new event planning and service marketplace. This repository contains the **Stage 1 development foundation**, not a production-ready platform.

## Stack
- React 19, TypeScript, Vite, Tailwind CSS 4
- Python FastAPI, SQLAlchemy 2, PostgreSQL 16
- Argon2 password hashing and database-backed HttpOnly sessions

## Prerequisites
Install Node.js 20.19+ or 22.12+, npm, Python 3.11+, and Docker with Compose (or a local PostgreSQL 16 server).

## Ubuntu quick start

```bash
git clone https://github.com/adokwu739-dotcom/plan-big.git
cd plan-big
docker compose up -d db
```

Start the API in terminal 1:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://planbig:planbig_dev@localhost:5432/planbig
python init_db.py
uvicorn app.main:app --reload
```

Start the frontend in terminal 2 (from the repository root):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 for the website or http://localhost:8000/docs for the API.

## How it works
The React app uses `fetch("/api/v1/...")`. During development Vite proxies `/api` requests to FastAPI on port 8000. FastAPI validates user data, hashes passwords, and stores users and login sessions in PostgreSQL. Login sets an HttpOnly cookie; React does not store a password or access token in localStorage.

## Important security and scope notes
This is a **local-development prototype**. Do not deploy it to production without adding CSRF protection for cookie-authenticated mutations, login rate limits, secure-cookie HTTPS configuration, Alembic migrations, email verification, password reset, monitoring, automated tests, and deployment hardening. The database credentials in docker-compose are development-only. Avoid exposing PostgreSQL publicly.

Stage 2 will implement events, provider profiles, services, bookings, and dashboards. Payments, messaging, and subscriptions are **not yet implemented**.

## Files
- `frontend/src/App.tsx`: starter pages and authentication forms
- `frontend/vite.config.ts`: API proxy and Tailwind plugin
- `backend/app/main.py`: API endpoints and models
- `backend/init_db.py`: local development database initialization
- `docker-compose.yml`: PostgreSQL development container

## Verify
```bash
cd frontend && npm run build
```
Visit `/api/v1/health` and register/login through the website. The project has not yet been verified in a deployed environment.
