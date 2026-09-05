# BHUMI-AI — Intelligent National Land Acquisition & Management Platform

[![SIH Problem Statement](https://img.shields.io/badge/SIH%202024-SIH26016-blue.svg)](https://www.sih.gov.in/)
[![Ministry](https://img.shields.io/badge/Ministry-Rural%20Development%20(MoRD)-green.svg)](https://rural.gov.in/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20SQLAlchemy%202.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%7C%20TypeScript%20%7C%20Vite-61DAFB.svg)](https://react.dev/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%2015%2B%20%7C%20PostGIS-336791.svg)](https://postgis.net/)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20SIH-orange.svg)]()

> **BHUMI-AI** is an end-to-end, AI-powered National Land Acquisition and Management Platform developed for **SIH26016 (Ministry of Rural Development)**. It unifies GIS spatial parcel mapping, RFCTLARR Act (2013) statutory lifecycle automation, compensation disbursement tracking, Rehabilitation & Resettlement (R&R) management, dispute monitoring, on-ground field officer verification, public citizen parcel tracking, predictive AI risk analysis, and conversational intelligence (BHUMI Copilot).

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Capabilities](#-key-capabilities)
- [System Architecture](#-system-architecture)
- [Repository Structure](#-repository-structure)
- [Technology Stack](#-technology-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
- [Environment Variables](#-environment-variables)
- [Database Setup & Migrations](#-database-setup--migrations)
- [Demo Credentials & Role-Based Access](#-demo-credentials--role-based-access)
- [Public Citizen Tracking Portal](#-public-citizen-tracking-portal)
- [AI Engine & BHUMI Copilot](#-ai-engine--bhumi-copilot)
- [Available Application Endpoints](#-available-application-endpoints)
- [Troubleshooting](#-troubleshooting)
- [Security & Compliance](#-security--compliance)

---

## 🌟 Overview

Land acquisition in India across national highways, railways, and industrial corridors is frequently constrained by:
1. Fragmented land records across state and district revenue authorities.
2. Protracted statutory compliance lifecycles under the RFCTLARR Act, 2013 (Section 4 preliminary surveys, Section 11 preliminary notifications, Section 19 declarations, Section 23 awards).
3. Litigations, title disputes, and delayed Direct Benefit Transfer (DBT) compensation.
4. Information asymmetry between acquiring authorities and project-affected citizens.

**BHUMI-AI** resolves these challenges by creating a single, authoritative digital operating picture:
- **OBSERVE**: Spatial GIS mapping of land parcels with boundary polygons, survey numbers, and ownership status.
- **UNDERSTAND**: Relational linkage between parcels, families, compensation awards, and active litigation.
- **PREDICT**: Machine learning risk engine that calculates project delay probability, cost escalation, and dispute bottlenecks.
- **RECOMMEND**: Actionable interventions (e.g., Lok Adalat dispute settlement batches, DBT clearance triggers).
- **ACT**: Automated workflow task assignment directly to field verification officers and district collectors.

---

## ⚡ Key Capabilities

| Module | Core Functionality |
|---|---|
| **National Command Center** | Real-time statutory KPIs, acquisition progress meters, state-wise budget utilization, and critical project alerts. |
| **State & District Drill-down** | Interactive administrative navigation from national overview to State level (e.g. Rajasthan, Maharashtra) down to individual districts (e.g. Jaipur, Pune). |
| **Interactive GIS Engine** | Leaflet + PostGIS interactive parcel visualization with color-coded statutory states (Not Acquired, Notified, Awarded, Disbursed, Possessed). |
| **RFCTLARR Statutory Workflow** | 7-stage statutory lifecycle tracking (Proposal → Preliminary Survey → Section 11 Notification → Section 19 Declaration → Award → Compensation → Possession). |
| **Compensation & DBT Tracking** | Granular disbursement monitoring, award declarations, bank transaction references, and DBT reconciliation status. |
| **R&R Management** | Rehabilitation and Resettlement entitlement tracking for Project-Affected Families (PAF) including housing grants and livelihood assistance. |
| **Dispute Resolution Hub** | Centralized legal case registry, court levels, stay orders, and risk recalculation upon case resolution. |
| **Field Officer Portal** | Mobile-responsive portal for field verification officers to record on-ground GPS coordinates, survey validation, and photo evidence. |
| **Citizen Transparency Portal** | Public, unauthenticated search portal where affected landowners can track land acquisition status, awards, and compensation by survey number. |
| **AI Risk & Anomaly Engine** | Evaluates delay probability, budget overrun risk, and flags anomalous valuation patterns across project parcels. |
| **BHUMI AI Copilot** | Grounded conversational AI assistant powered by Google Gemini (with an intelligent, database-grounded local reasoning fallback). |
| **Statutory Audit Trail** | Immutable log recording every user action, approval, dispute update, and AI recommendation execution. |

---

## 🏛️ System Architecture

```
                                  ┌─────────────────────────────────────────┐
                                  │           BHUMI-AI WEB CLIENT           │
                                  │   React 19 + TypeScript + Vite + CSS    │
                                  └────────────────────┬────────────────────┘
                                                       │
                                            HTTP / JSON (REST API)
                                                       │
                                                       ▼
                                  ┌─────────────────────────────────────────┐
                                  │             FASTAPI BACKEND             │
                                  │               Port: 8000                │
                                  └─┬─────────┬─────────┬─────────┬───────┬─┘
                                    │         │         │         │       │
              ┌─────────────────────┘         │         │         │       └─────────────────────┐
              ▼                               ▼         ▼         ▼                             ▼
   ┌───────────────────────┐         ┌─────────────────────────┐ ┌───────────────────┐ ┌───────────────────┐
   │  Authentication/RBAC  │         │     Domain Routers      │ │   AI Services     │ │  Citizen Portal   │
   │  - JWT Bearer Tokens  │         │  - Projects & Parcels   │ │  - Risk Engine    │ │  - Public Search  │
   │  - Passlib (Bcrypt)   │         │  - Workflow & Tasks     │ │  - Anomaly Engine │ │  - Parcel Status  │
   │  - 7 Role Profiles    │         │  - Compensation & DBT   │ │  - Gemini LLM     │ │  - Compensation   │
   └───────────────────────┘         │  - Disputes & R&R       │ │  - Local Fallback │ └───────────────────┘
                                     │  - Field Verification   │ └─────────┬─────────┘
                                     │  - System Notifications │           │
                                     │  - Audit Trail          │           ▼
                                     └────────────┬────────────┘  ┌───────────────────┐
                                                  │               │ Google Gemini API │
                                                  ▼               │ (Optional / HTTPS)│
                                     ┌─────────────────────────┐  └───────────────────┘
                                     │   SQLAlchemy 2.0 ORM    │
                                     │   (Async Engine asyncpg)│
                                     └────────────┬────────────┘
                                                  │
                                                  ▼
                                     ┌─────────────────────────┐
                                     │  PostgreSQL 15+ + PostGIS│
                                     │   (Supabase / Postgres) │
                                     └─────────────────────────┘
```

---

## 📁 Repository Structure

```
BHUMI-AI/
├── README.md                      # Primary Project Documentation (This File)
├── .gitignore                     # Git Exclusion Rules
│
├── backend/                       # FastAPI Backend Application
│   ├── README.md                  # Backend Specific Guide & API Documentation
│   ├── requirements.txt           # Python Dependencies (pip)
│   ├── .env.example               # Template for Backend Environment Variables
│   ├── alembic.ini                # Alembic Migration Configuration
│   │
│   ├── alembic/                   # Database Migrations
│   │   ├── env.py                 # Sync Psycopg2 Migration Runtime
│   │   └── versions/              # Migration Scripts (0001_initial_schema.py)
│   │
│   ├── app/                       # Application Source Code
│   │   ├── main.py                # FastAPI App Entry Point, CORS, Router Ingestion
│   │   ├── config.py              # Pydantic BaseSettings (.env loader)
│   │   ├── database.py            # Async Engine (asyncpg) & DB Session Dependency
│   │   ├── domain_routers.py      # Unified Routers (Compensation, Disputes, Docs, etc.)
│   │   │
│   │   ├── ai/                    # AI Copilot, Risk Engine & LLM Provider
│   │   │   ├── router.py          # /api/ai Endpoints (Risk, Anomalies, Copilot)
│   │   │   ├── provider.py        # GeminiProvider & LocalFallbackProvider
│   │   │   └── tools.py           # Database Context Aggregation for AI
│   │   │
│   │   ├── analytics/             # /api/analytics (National & State Rollups)
│   │   ├── audit/                 # Statutory Audit Log Service
│   │   ├── auth/                  # JWT Authentication, Password Hashing & RBAC
│   │   ├── models/                # SQLAlchemy ORM Models
│   │   │   ├── base.py            # Base & Timestamp Mixin
│   │   │   ├── enums.py           # PostgreSQL Native Enum Types
│   │   │   ├── user.py            # User Entity
│   │   │   ├── project.py         # Project Entity
│   │   │   ├── land_parcel.py     # LandParcel + PostGIS Geometry
│   │   │   ├── compensation.py    # Compensation Disbursements
│   │   │   ├── family.py          # Project-Affected Families (R&R)
│   │   │   └── ...                # Disputes, Documents, Tasks, Notifications
│   │   │
│   │   ├── parcels/               # /api/parcels (GIS Queries & GeoJSON)
│   │   ├── projects/              # /api/projects (Project Lifecycle & CRUD)
│   │   ├── proposals/             # Proposal Management
│   │   └── rr/                    # /api/rr (Rehabilitation & Resettlement)
│   │
│   └── scripts/                   # CLI & Seed Scripts
│       ├── seed.py                # Database Seeder (Demo Data, Parcels, Users)
│       └── test_module*.py        # Verification Scripts
│
└── frontend/                      # React 19 Frontend Application
    ├── README.md                  # Frontend Specific Guide & Component Guide
    ├── package.json               # Node Dependencies and Scripts
    ├── tsconfig.json              # TypeScript Configuration
    ├── vite.config.ts             # Vite 8 Build Configuration
    │
    ├── public/                    # Static Assets
    └── src/                       # React Application Source
        ├── main.tsx               # DOM Mounting Point
        ├── App.tsx                # Client Routing & Role-Guarded Protected Routes
        ├── index.css              # Global Design Tokens, Layout, High-Contrast Themes
        │
        ├── api/                   # Backend Communication
        │   └── client.ts          # Typed Fetch API Client (Token Injection)
        │
        ├── contexts/              # Global React State
        │   └── AuthContext.tsx    # Auth State, Login/Logout, LocalStorage
        │
        ├── components/            # Reusable UI Components
        │   ├── Layout.tsx         # Responsive Shell, High-Contrast Sidebar, Header
        │   ├── Login.tsx          # 60/40 Split Auth Screen + 1-Click Demo Evaluation
        │   ├── Map.tsx            # Leaflet PostGIS GIS Visualization & Color Codes
        │   ├── NotificationDropdown.tsx # Functional Bell Dropdown & Read Actions
        │   └── ...
        │
        └── pages/                 # Full Page Views
            ├── Dashboard.tsx      # National Command Center
            ├── StateDashboard.tsx # State Admin Drill-down View
            ├── Projects.tsx       # Project Directory & Filters
            ├── ProjectDetail.tsx  # Project Details, Embedded GIS, Statutory Tabs
            ├── Compensation.tsx   # DBT & Compensation Disbursement Ledger
            ├── Disputes.tsx       # Legal Case Tracking & Dispute Resolution
            ├── RRManagement.tsx   # Rehabilitation & Resettlement Records
            ├── Documents.tsx      # Document Repository & AI Intelligence
            ├── Workflow.tsx       # Statutory Tasks & Approval Pipeline
            ├── FieldDashboard.tsx # Field Verification Portal
            ├── CitizenPortal.tsx  # Public Landowner Tracking Portal
            ├── AuditLog.tsx       # Compliance Audit Trail
            └── Analytics.tsx      # Multi-dimensional Data Visualizations
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) 0.104+ (Asynchronous Python Web Framework)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/) 0.24+
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) 2.0+ (Declarative 2.0 Async/Sync Mapping)
- **Spatial Extension**: [GeoAlchemy2](https://geoalchemy2.readthedocs.io/) 0.14+ (PostGIS integration)
- **Async Database Driver**: [asyncpg](https://github.com/MagicStack/asyncpg) 0.29+ (Used at runtime by FastAPI)
- **Sync Database Driver**: [psycopg2-binary](https://www.psycopg.org/) 2.9+ (Used by Alembic and Seed scripts)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/) 1.13+
- **Configuration & Validation**: [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **Security & Auth**: [passlib](https://passlib.readthedocs.io/) (bcrypt password hashing) & [python-jose](https://python-jose.readthedocs.io/) (JWT encoding/decoding)
- **AI Integration**: [Google Gemini REST API](https://ai.google.dev/) via `httpx` with deterministic local fallback

### Frontend
- **Framework**: [React](https://react.dev/) 19.2+ with [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite](https://vitejs.dev/) 8.2+
- **Routing**: [React Router](https://reactrouter.com/) 7.18+
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) v4 & Custom Semantic Design System (WCAG AAA High-Contrast)
- **GIS & Mapping**: [Leaflet](https://leafletjs.com/) 1.9+ & [React-Leaflet](https://react-leaflet.js.org/) 5.0+
- **Charts & Data Viz**: [Recharts](https://recharts.org/) 3.10+
- **Icons**: [Lucide React](https://lucide.dev/)

### Database
- **Database Engine**: [PostgreSQL](https://www.postgresql.org/) 15+
- **Spatial Extension**: [PostGIS](https://postgis.net/) (Must be enabled: `CREATE EXTENSION IF NOT EXISTS postgis;`)
- **Hosting Options**: Compatible with Supabase, AWS RDS, Cloud SQL, or local PostgreSQL.

---

## 📋 Prerequisites

Before running the application, ensure the following software is installed on your machine:

1. **Python**: Version `3.10` or higher (`python3 --version`).
2. **Node.js**: Version `18.0.0` or higher (`node --version`).
3. **npm**: Version `9.0.0` or higher (`npm --version`).
4. **PostgreSQL**: PostgreSQL 15+ instance with the `postgis` extension enabled (or an active Supabase project).
5. **Git**: Installed and configured on your system.

---

## 🚀 Quick Start Guide

Follow these step-by-step instructions to get the complete BHUMI-AI platform running locally.

### 1. Clone Repository

```bash
git clone https://github.com/Adj251006/BHUMI-AI.git
cd BHUMI-AI
```

---

### 2. Backend Setup

#### Step 2.1 — Navigate to backend & create Python virtual environment
```bash
cd backend
python3 -m venv venv
```

Activate the virtual environment:
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```
- **Windows (Command Prompt)**:
  ```cmd
  venv\Scripts\activate.bat
  ```
- **Windows (PowerShell)**:
  ```powershell
  venv\Scripts\Activate.ps1
  ```

#### Step 2.2 — Install Python dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 2.3 — Configure environment variables
Create a `.env` file in the `backend/` directory:
```bash
cp .env.example .env
```

Edit `backend/.env` with your actual PostgreSQL connection string:
```ini
# PostgreSQL with PostGIS connection string
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@[YOUR_HOST]:5432/postgres?sslmode=require

# Application Secret Key for JWT token signing
SECRET_KEY=your-secure-random-secret-key-min-32-chars

# Runtime Environment (development | staging | production)
ENVIRONMENT=development

# AI Provider Configuration (Optional)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-google-gemini-api-key-here
```
> [!NOTE]
> If you do not provide a `GEMINI_API_KEY`, BHUMI-AI will automatically run its built-in database-grounded reasoning engine (`LocalFallbackProvider`). The application will **not** crash or fail without an API key.

#### Step 2.4 — Run database migrations
Ensure PostGIS is enabled on your PostgreSQL database (`CREATE EXTENSION IF NOT EXISTS postgis;`), then run:
```bash
alembic upgrade head
```

#### Step 2.5 — Seed sample demonstration data
Seed projects, parcels, compensation awards, disputes, and demo user accounts:
```bash
python -m scripts.seed
```
*(Note: The seed script is idempotent. It will safely skip if data already exists, or you can re-seed with `python -m scripts.seed --force`.)*

#### Step 2.6 — Start the FastAPI backend server
```bash
uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
```

Backend is now operational at:
- **API Base**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

### 3. Frontend Setup

Open a new terminal window or tab.

#### Step 3.1 — Navigate to frontend
```bash
cd frontend
```

#### Step 3.2 — Install Node packages
```bash
npm install
```

#### Step 3.3 — Start the Vite development server
```bash
npm run dev
```

The frontend will start at:
- **Web Application**: `http://localhost:5173` (or `http://127.0.0.1:5173`)
- **Public Citizen Tracking Portal**: `http://localhost:5173/citizen`

#### Step 3.4 — Verify production build (Optional)
To verify that the frontend compiles cleanly for production:
```bash
npm run build
```

---

## 🔑 Demo Credentials & Role-Based Access

The login page (`/login`) features a responsive 60/40 split design with **1-Click Instant Demo Authentication** cards for SIH evaluators.

Clicking any demo card authenticates immediately and routes to that role's authorized workspace:

| Role Profile | Demo Email | Demo Password | System Role | Destination Route | Key Capabilities |
|---|---|---|---|---|---|
| **🏛️ Central Admin** | `admin@mord.gov.in` | `admin123` | `central_ministry` | `/dashboard` | National Command Center, macro KPIs, national budget oversight, AI simulations. |
| **🏛️ State Admin** | `rajasthan@gov.in` | `state123` | `state_govt` | `/state/Rajasthan` | State-level project rollups, district performance monitoring, state approvals. |
| **🏢 District Officer** | `jaipur@gov.in` | `district123` | `district_authority` | `/projects` | District project directory, parcel acquisition reviews, Section 11/19 clearances. |
| **🏗️ Project Agency** | `rj-hwy@nhia.in` | `project123` | `project_agency` | `/project/12345678-1234-5678-1234-567812345678` | Specific highway execution view (Delhi-Jaipur Expansion), parcel lists, embedded GIS. |
| **📍 Field Officer** | `field.rahul@gov.in` | `field123` | `field_officer` | `/field` | On-ground field inspection portal, GPS verification submissions, survey photos. |
| **🔒 Auditor** | `auditor@mord.gov.in` | `audit123` | `auditor` | `/audit` | Immutable audit trail, compliance verification, dispute & compensation logs. |
| **👤 Citizen** | `citizen@example.com` | `citizen123` | `citizen` | `/citizen` | Landowner view (Can also be accessed publicly without any login). |

---

## 🌐 Public Citizen Tracking Portal

In compliance with statutory transparency guidelines and the **Digital Personal Data Protection (DPDP) Act, 2023**, BHUMI-AI provides a dedicated public tracking portal:

- **Public URL**: `http://localhost:5173/citizen`
- **Backend API**: `GET /api/citizen/track/{parcel_reference}`
- **Sample Search Query**: Try searching survey number `100/1` or `100/2`.
- **Outputs**:
  - Verification of parcel ownership and village details.
  - 7-stage statutory lifecycle progress bar (Preliminary Notification → Possession).
  - Assessed compensation award amount vs. disbursed amount.
  - Payment reference and grievance contact.

---

## 🤖 AI Engine & BHUMI Copilot

BHUMI-AI features a dual-layer AI decision-support architecture:

### 1. Conversational AI Copilot (`POST /api/ai/copilot`)
- **Natural Language Understanding**: Users can ask arbitrary questions (e.g., *"What is the status of RJ-HWY-024?"*, *"Why is this project at risk?"*, *"Which parcels are causing the bottleneck?"*).
- **Context-Grounded**: Ingests real database records for the currently selected project or parcel before prompting the LLM.
- **Strict Anti-Hallucination**: If data is missing in the database, the assistant explicitly states: *"I don't have enough information in the current BHUMI-AI data to answer that."*
- **LLM Provider (`GeminiProvider`)**: Connects to Google Gemini (`gemini-flash-latest` / Gemini REST API) via `GEMINI_API_KEY`.
- **Local Fallback Engine (`LocalFallbackProvider`)**: When no API key is supplied, a deterministic rules-based reasoning engine generates accurate responses directly from PostgreSQL tables.
- **Action Execution**: Copilot suggestions can trigger real application actions (e.g. creating a `WorkflowTask` for field officers).

### 2. Predictive Risk Engine (`GET /api/ai/risk/{project_id}`)
- Analyzes open disputes, pending DBT compensation records, and overdue tasks strictly scoped to that project.
- Computes:
  - Overall Risk Score (0–100) and Risk Level (Low, Medium, High, Critical).
  - Delay probability and estimated timeline slip (in days).
  - Estimated cost escalation percentage.
  - Identified critical bottleneck parcels.

### 3. Anomaly Detection (`GET /api/ai/anomalies`)
- Scans parcels across all projects to identify valuation discrepancies, irregular area variances, or compensation anomalies.

---

## 🔗 Available Application Endpoints

### Frontend Routes (Port 5173)
- `/login` — Login screen with 60/40 layout and 1-Click Demo Evaluation buttons.
- `/dashboard` — National Command Center (Admin/Ministry).
- `/state/:stateName` — State-level executive overview.
- `/projects` — Comprehensive project catalog with search and filters.
- `/project/:id` — In-depth project view with embedded GIS map and parcel inspector.
- `/compensation` — Compensation disbursements and DBT payment tracking.
- `/disputes` — Dispute resolution portal and court litigation tracking.
- `/rr` — Rehabilitation & Resettlement (R&R) entitlements and grants.
- `/documents` — Document repository with AI metadata analysis.
- `/workflow` — Statutory workflow task queue and approvals.
- `/simulator` — What-If policy & timeline simulation engine.
- `/analytics` — State and national analytics with interactive charts.
- `/field` — Field verification officer mobile portal.
- `/citizen` — Public citizen parcel tracking portal.
- `/audit` — Tamper-evident statutory audit log.

### Backend API Documentation (Port 8000)
- `GET /health` — Service health and database connectivity check.
- `GET /docs` — Interactive Swagger UI (test endpoints directly in browser).
- `GET /redoc` — ReDoc formatted API specifications.
- `POST /auth/login` — OAuth2/JWT token generation.
- `GET /auth/me` — Current authenticated user profile.
- `GET /api/projects` — List land acquisition projects.
- `GET /api/parcels` — Fetch parcels and GeoJSON polygon boundaries.
- `GET /api/ai/risk/{project_id}` — Calculate predictive project risk.
- `POST /api/ai/copilot` — Grounded AI Copilot query endpoint.
- `GET /api/citizen/track/{parcel_reference}` — Public parcel tracking.
- `GET /api/notifications` — Retrieve system notifications.
- `PUT /api/notifications/read-all` — Mark notifications as read.

---

## 🔧 Troubleshooting

### 1. Database Connection Failure (`asyncpg.exceptions` or `OperationalError`)
- Verify that your `DATABASE_URL` in `backend/.env` is correct and accessible.
- If using Supabase or cloud PostgreSQL, verify that your IP address is not blocked by firewall rules and that `?sslmode=require` is present.
- Ensure the PostGIS extension is enabled by running:
  ```sql
  CREATE EXTENSION IF NOT EXISTS postgis;
  ```

### 2. Alembic Migration Error (`Can't locate revision`)
- Check migration history in the database:
  ```bash
  cd backend
  source venv/bin/activate
  alembic current
  ```
- If the database was created fresh, run:
  ```bash
  alembic upgrade head
  ```

### 3. Port Conflicts
- If port `8000` is already in use:
  ```bash
  uvicorn app.main:app --port 8001 --reload
  ```
- If port `5173` is already in use:
  Vite will automatically offer port `5174`. Update `src/api/client.ts` if running on non-standard backend ports.

### 4. Node / npm Command Not Found (macOS)
- Ensure Node.js is in your terminal PATH:
  ```bash
  export PATH=/usr/local/bin:/opt/homebrew/bin:$PATH
  ```

---

## 🔒 Security & Compliance

- **Authentication**: Salted Bcrypt password hashing (`passlib`) with HMAC-SHA256 JWT tokens.
- **RBAC**: Strict role enforcement preventing unauthorized role route access.
- **Citizen Privacy**: The public citizen tracking endpoint exposes only statutory survey progress; confidential banking and personal owner IDs are masked in accordance with the **DPDP Act, 2023**.
- **Audit Logging**: All sensitive mutations (approvals, dispute closures, DBT triggers) generate tamper-evident records in the `audit_logs` table.

---

## 🏆 SIH26016 Evaluation Demo Workflow

For evaluators reviewing BHUMI-AI:
1. Open `http://localhost:5173`.
2. Click **🏛️ Central Admin** for instant login to the **National Command Center**.
3. Inspect national KPIs, state rollups, and the notification bell dropdown in the top navigation.
4. Click **Projects** in the sidebar → Select **Delhi-Jaipur Highway Expansion**.
5. Switch to the **GIS Land Parcels** tab → Click on any parcel to inspect real PostGIS geometry, ownership, and award status.
6. Open **BHUMI Copilot** in the bottom-right corner and ask:
   *"Why is this project at risk?"* or *"What is the bottleneck for RJ-HWY-024?"*
7. Open a separate browser tab to `http://localhost:5173/citizen` and search for survey number `100/1` to verify the public transparency portal.
8. Log in as **📍 Field Officer** (`field.rahul@gov.in` / `field123`) to test the field verification submission.
9. Log in as **🔒 Auditor** (`auditor@mord.gov.in` / `audit123`) to view the tamper-evident audit trail.

---

*Developed for Smart India Hackathon 2024 · Ministry of Rural Development · BHUMI-AI Team*
