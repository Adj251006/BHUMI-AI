# BHUMI-AI Backend — FastAPI Application

> **Intelligent National Land Acquisition & Management Platform**  
> Problem Statement: **SIH26016** · Ministry of Rural Development

The BHUMI-AI backend is an asynchronous, high-performance REST API built with **FastAPI**, **SQLAlchemy 2.0**, **GeoAlchemy2**, and **PostGIS**. It powers spatial parcel processing, RFCTLARR Act (2013) statutory lifecycles, compensation disbursement tracking, role-based access control, machine learning risk engines, and conversational AI assistance.

---

## 🛠️ Technology Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Async Python 3.10+)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/) (with standard event loops)
- **Database ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async engine + declarative ORM)
- **Spatial Geometry**: [GeoAlchemy2](https://geoalchemy2.readthedocs.io/) (PostGIS geometry and spatial queries)
- **Async Database Driver**: [asyncpg](https://github.com/MagicStack/asyncpg) (Fast asynchronous driver for runtime DB access)
- **Sync Database Driver**: [psycopg2-binary](https://www.psycopg.org/) (Synchronous driver used by Alembic and Seed scripts)
- **Database Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Configuration & Settings**: [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (Validates `.env` at startup)
- **Authentication**: [python-jose](https://python-jose.readthedocs.io/) (HMAC-SHA256 JWT tokens) & [passlib[bcrypt]](https://passlib.readthedocs.io/) (Bcrypt password hashing)
- **AI Decision Support**: Google Gemini API via `httpx` with built-in database-grounded local reasoning fallback

---

## 📁 Backend Directory Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── env.py                  # Alembic migration runner (uses psycopg2 sync driver)
│   ├── script.py.mako          # Migration template
│   └── versions/               # Schema revisions (0001_initial_schema.py)
│
├── app/                        # Application source code
│   ├── main.py                 # FastAPI app initialization, CORS, router mounting
│   ├── config.py               # Pydantic Settings class loading .env
│   ├── database.py             # Async SQLAlchemy engine (asyncpg) & get_db dependency
│   ├── domain_routers.py       # Routers for Compensation, Disputes, Documents, Workflow, etc.
│   │
│   ├── ai/                     # AI Decision Support Engine
│   │   ├── router.py           # /api/ai endpoints (risk calculation, anomalies, copilot)
│   │   ├── provider.py         # GeminiProvider & LocalFallbackProvider abstraction
│   │   └── tools.py            # Aggregates real DB context (projects, parcels, disputes)
│   │
│   ├── analytics/              # /api/analytics (National & State-level rollups)
│   ├── audit/                  # /api/audit (Immutable statutory audit logs)
│   ├── auth/                   # /auth (JWT authentication, login, me, and RBAC)
│   │   ├── router.py           # Login and profile endpoints
│   │   ├── security.py         # Password hashing & JWT token issuance/verification
│   │   └── dependencies.py     # FastAPI dependencies for current_user & require_role
│   │
│   ├── models/                 # SQLAlchemy 2.0 ORM Models
│   │   ├── base.py             # Base declarative class with timestamp mixins
│   │   ├── enums.py            # PostgreSQL native ENUM types (UserRole, ProjectStatus, etc.)
│   │   ├── user.py             # User accounts & roles
│   │   ├── project.py          # Land acquisition projects
│   │   ├── land_parcel.py      # Parcels with PostGIS geometry (POLYGON)
│   │   ├── proposal.py         # Acquisition proposals
│   │   ├── notification.py     # Section 4/11 statutory gazette notifications
│   │   ├── award.py            # Compensation awards under Section 23/27
│   │   ├── compensation.py     # Direct Benefit Transfer (DBT) disbursements
│   │   ├── family.py           # Project-Affected Families (R&R entitlements)
│   │   └── ...                 # Disputes, documents, tasks, notifications, audit logs
│   │
│   ├── parcels/                # /api/parcels (PostGIS spatial queries & GeoJSON outputs)
│   ├── projects/               # /api/projects (Project lifecycle management & metrics)
│   ├── proposals/              # /proposals (Proposal review pipeline)
│   └── rr/                     # /api/rr (Rehabilitation and Resettlement modules)
│
├── scripts/                    # CLI utilities and test suites
│   ├── seed.py                 # Comprehensive idempotent database seeder
│   ├── test_module2.py         # Module 2 test suite
│   ├── test_module3.py         # Module 3 test suite
│   └── test_module4.py         # Module 4 test suite
│
├── requirements.txt            # Python dependencies
├── alembic.ini                 # Alembic configuration
├── .env.example                # Template for environment variables
└── README.md                   # This file
```

---

## ⚙️ Environment Configuration

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

### Environment Variable Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | — | PostgreSQL connection string with PostGIS enabled. Format: `postgresql://user:password@host:port/dbname?sslmode=require` |
| `SECRET_KEY` | **Yes** | — | Cryptographic secret for signing JWT access tokens (minimum 32 characters recommended). |
| `ENVIRONMENT` | No | `development` | Runtime environment (`development`, `staging`, `production`). In development, SQL query logging is enabled. |
| `LLM_PROVIDER` | No | `gemini` | AI LLM provider to use for BHUMI Copilot (`gemini` or `local_fallback`). |
| `GEMINI_API_KEY` | No | `""` | Google Gemini API key. If omitted or empty, the backend automatically uses `LocalFallbackProvider` (grounded database reasoning). |

---

## 🚀 Setup & Execution

### 1. Create Virtual Environment & Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Prepare Database & Run Migrations

Ensure your PostgreSQL instance has PostGIS enabled:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Run Alembic migrations to construct the database schema:
```bash
alembic upgrade head
```

### 3. Seed Demonstration Data

The seed script initializes sample infrastructure projects (e.g. *Delhi-Jaipur Highway Expansion*, *Mumbai-Pune Expressway Expansion*), PostGIS parcels, compensation awards, active disputes, workflow tasks, and predefined demo accounts:

```bash
python -m scripts.seed
```

*(Note: If data already exists, the script safely skips insertion. Pass `--force` or `-f` to force re-seeding.)*

### 4. Start Development Server

```bash
uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
```

---

## 📡 Key API Endpoints

FastAPI provides automated interactive documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

### Authentication (`/auth` and `/api/auth`)
- `POST /auth/login` — Authenticate with email/password; returns JWT access token.
- `GET /auth/me` — Retrieve the profile and role of the currently authenticated user.

### Projects & GIS Parcels
- `GET /api/projects` — List projects with state/ministry filters.
- `GET /api/projects/{id}` — In-depth project details and statutory KPIs.
- `GET /api/parcels?project_id={id}` — Spatial parcels formatted with PostGIS WKT/GeoJSON boundaries.
- `GET /api/parcels/{id}` — Individual parcel details, owner records, and award history.

### AI Decision Support
- `GET /api/ai/risk/{project_id}` — Calculate predictive project risk score, delay days, and cost escalation strictly scoped to the project.
- `GET /api/ai/anomalies` — Multi-project anomaly detector flagging irregular valuations and survey discrepancies.
- `POST /api/ai/copilot` — Natural language Copilot endpoint with grounded database context ingestion and optional Google Gemini generation.
- `POST /api/ai/recommendations/execute` — Execute AI-suggested risk mitigation actions (creates `WorkflowTask` records and audit logs).

### Operations & Citizen Portal
- `GET /api/compensation?project_id={id}` — Compensation disbursement ledger.
- `PUT /api/compensation/{id}/status` — Update DBT compensation payment status.
- `GET /api/disputes?project_id={id}` — Active disputes and litigation records.
- `PUT /api/disputes/{id}/resolve` — Resolve a dispute and trigger automated project risk recalculation.
- `GET /api/workflow/tasks?project_id={id}` — Statutory workflow task queue.
- `POST /api/field/verify` — Submit on-ground field inspection data with GPS coordinates and photos.
- `GET /api/citizen/track/{parcel_reference}` — Public, unauthenticated citizen tracking endpoint for survey numbers (e.g. `100/1`).
- `GET /api/notifications` — Retrieve role-specific system notifications.
- `PUT /api/notifications/read-all` — Mark all system notifications as read.
- `GET /api/audit` — Query immutable statutory audit logs.

---

## 🔒 Security & RBAC Enforcement

The backend enforces Role-Based Access Control via FastAPI dependencies in `app/auth/dependencies.py`:

```python
@router.post("/execute", dependencies=[Depends(require_role([UserRole.CENTRAL_MINISTRY, UserRole.DISTRICT_AUTHORITY]))])
async def execute_action(...):
    ...
```

Passwords are hashed with Bcrypt before persistence, and API endpoints validate JWT expiration and signature on every authenticated request.
