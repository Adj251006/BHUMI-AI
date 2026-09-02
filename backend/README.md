# National Land Acquisition & Management System — Backend

**SIH26016 · Ministry of Rural Development**

## Tech Stack

- **Framework:** FastAPI (async)
- **ORM:** SQLAlchemy 2.0 + GeoAlchemy2 (PostGIS)
- **Database:** PostgreSQL 15+ with PostGIS (hosted on Supabase)
- **Migrations:** Alembic

## Setup

### 1. Create virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your Supabase database URL and secret key
```

### 4. Enable PostGIS on Supabase

In your Supabase dashboard: **Database → Extensions → Search "postgis" → Enable**

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Seed sample data (development only)

```bash
python -m scripts.seed
```

### 7. Start the development server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Health check: `http://localhost:8000/health`

## Project Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration scripts
│   ├── env.py                  # Alembic environment config
│   └── script.py.mako          # Migration file template
├── app/
│   ├── config.py               # Settings via pydantic-settings
│   ├── database.py             # SQLAlchemy async engine + session
│   ├── main.py                 # FastAPI entry point
│   └── models/                 # SQLAlchemy ORM models
│       ├── base.py             # Declarative base + mixins
│       ├── enums.py            # PostgreSQL enum types
│       ├── user.py             # Users / RBAC
│       ├── project.py          # Land acquisition projects
│       ├── land_parcel.py      # Parcels + PostGIS geometry
│       ├── proposal.py         # Proposal workflow
│       ├── notification.py     # Legal notices
│       ├── award.py            # Compensation awards
│       ├── compensation.py     # Disbursement tracking
│       └── family.py           # R&R for affected families
├── scripts/
│   └── seed.py                 # Development seed data
├── requirements.txt
├── alembic.ini
└── .env.example
```
