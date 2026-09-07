# BHUMI-AI — Full Project Audit
**Date:** 5 Sep 2026 · **PS:** SIH26016 (MoRD) · **Deadline:** 20 Sep 2026

Audit covers: backend (`backend/app`, `backend/scripts`), frontend (`frontend/src`),
build/tooling, repo hygiene, and SIH-judging readiness.

## Verdict

The project is **broad and well-structured** — 13k LOC, 14 pages, ~50 endpoints,
clean auth layer, real SQLAlchemy 2.0 async models, real PostGIS geometry.
TypeScript build passes with zero errors. That is well above the median SIH build.

The problem is **depth vs. surface**. A large share of what the UI shows is
hardcoded in JSX, and several backend paths are dead on arrival (broken enum,
shadowed route, wrong FK). The evaluator questions listed on the PS page
("where does your data come from", "does it degrade gracefully", "production
scale") land directly on the weakest parts of this build.

**Ranking of what to spend remaining time on:**
1. Fix the 6 dead-on-arrival bugs (2 hours) — these are demo-killers.
2. Replace frontend hardcoded numbers with API data (1 day) — this is the credibility fix.
3. Make the AI defensible (half day) — label it honestly, fix the saturating score.
4. Everything else.

---

## P0 — Broken right now (fix today)

| # | Issue | File | Fix |
|---|---|---|---|
| 1 | `CompensationStatus.UNDER_VERIFICATION` doesn't exist — the member lives on an unused `CompensationStatusExtended`. Raises `AttributeError`, swallowed by a bare `except: pass` in the copilot, so **every copilot call silently loses compensation/R&R/task context and answers from hardcoded defaults**. | `models/enums.py:163,197`, `ai/tools.py:136`, `ai/router.py:141` | Add `UNDER_VERIFICATION = "under_verification"` to `CompensationStatus`; delete `CompensationStatusExtended`; remove the bare except. |
| 2 | `POST /api/compensation/{id}/assign-verification` writes `project_id=comp.award_id` — an Award UUID into a FK pointing at `projects.id`. Always 500s. | `domain_routers.py:116` | Join Award → LandParcel to get the real `project_id`. |
| 3 | `GET /api/parcels/spatial` is declared **after** `/{parcel_id}`, so FastAPI matches it as a UUID and returns 422. The map's bbox search is unreachable. | `parcels/router.py:47,93` | Move `/spatial` and `/project/{id}` above `/{parcel_id}`. |
| 4 | `Family.is_eligible_for_resettlement` / `.resettlement_status` don't exist (model has `r_and_r_status`). `get_rr_summary` throws. | `ai/tools.py:167` | Count on `r_and_r_status in (PLAN_APPROVED, RESETTLED)`. |
| 5 | **Leaflet CSS is never imported.** Tiles stack diagonally, popups and zoom controls unstyled. The GIS module — the PS's headline ask — looks broken on screen. | `main.tsx` | `import 'leaflet/dist/leaflet.css'` |
| 6 | `requirements.txt` is missing `httpx` and `shapely`, both imported directly. A clean `pip install -r requirements.txt` on a judge's machine → ImportError on the copilot and the geo-tagging route. | `requirements.txt` | Add `httpx`, `shapely`, `bcrypt`; drop `passlib` (unused). |

Also: `seed.py:64` runs `ALTER TYPE compensation_status ADD VALUE 'under_verification'`
on the live PG type while the Python enum lacks it — any row written with that
value becomes unreadable by the ORM (`LookupError` → 500 on `GET /api/compensation`).
Fixing #1 resolves this too.

## P0 — Security holes a judge will find in 30 seconds

| # | Issue | File |
|---|---|---|
| 7 | All four parcel/GIS read endpoints have **no auth dependency**. Full land records + geometry are public. | `parcels/router.py:19,47,93,114` |
| 8 | `/api/citizen/track/{ref}` is unauthenticated and does `survey_number ILIKE '%ref%' LIMIT 1` — passing `1` or `/` enumerates real owner names, compensation amounts and NEFT payment references. | `main.py:104` |
| 9 | `PUT /documents/{id}/status` and `PUT /workflow/tasks/{id}/status` have **zero RBAC** — any authenticated user, including a citizen account, can approve documents and close tasks. | `domain_routers.py:270,335` |
| 10 | `mark_read` has no ownership check — any user can mark any other user's notification read. | `domain_routers.py:547` |
| 11 | `allow_origins=["*"]` **with** `allow_credentials=True` — an invalid combination browsers reject, and an automatic finding on any security review. | `main.py:63` |
| 12 | Demo passwords (`admin@mord.gov.in / admin123` ×6 roles) are rendered in the UI and shipped in the JS bundle. Fine as a demo affordance — gate it behind `import.meta.env.DEV`. | `Login.tsx:15-70` |
| 13 | Gemini API key is passed in the **URL query string** (`provider.py:95`); errors go to `print()`. | `ai/provider.py:95,115` |

> `.env` is correctly gitignored and not tracked — good. But the live Supabase
> password and Gemini key are in it; rotate both before you publish the repo.

## P1 — The credibility problem: hardcoded data

This is the single biggest risk to your score. **If a judge stops the backend,
the dashboard looks identical.** Every item below is a number invented in JSX:

- `Login.tsx:273` — "28 States / ₹2,400Cr / 15,000+ Parcels"
- `Layout.tsx:17-63` — 5 fabricated notifications, shown when the API fails **or returns empty**
- `Layout.tsx:69` — sidebar badges `52` and `18`, never from API
- `Dashboard.tsx:27` — `MOCK_TIMELINE`, rendered under a **"Live"** badge
- `Dashboard.tsx:71` — entire "Projects by Sector" chart
- `Dashboard.tsx:99-123` — every KPI has a `?? 22`-style fallback that renders when the backend is down
- `Dashboard.tsx:224-232` — "Projects Requiring Action" top-5 list (Gujarat Bullet Train 91% …)
- `Dashboard.tsx:285` — "AI Anomaly Feed", 4 hardcoded anomalies
- `Analytics.tsx:26,33` — risk-distribution pie and monthly-trend chart
- `Compensation.tsx:53` — "AI Anomaly Detected: ₹1.8Cr — 4.2× district average"
- `Disputes.tsx:46` — "7 Critical Disputes … reduce delay risk by 29%"
- `Simulator.tsx:4,63-101` — slider maxes, captions, and a single hardcoded project UUID
- `FieldDashboard.tsx:9-38` — GPS pre-filled to Jaipur and `registered_lat/lon` hardcoded, so **GPS-mismatch detection is theatre**
- Hardcoded demo UUIDs in 6 files

**Fix:** wire each to its API field, and replace every `?? <number>` fallback with
an explicit "Backend unavailable" state. A dashboard that honestly says "no data"
scores higher than one that invents it.

## P1 — The AI has to survive one follow-up question

Judges will ask "how does this work?" — right now the answers are:

- **Risk engine** (`ai/router.py:473`) is a 3-term linear constant:
  `disputes×0.04 + pending_comp×0.01 + overdue_tasks×0.05`, clamped to 1.0.
  With the seeded RJ-HWY project (12 disputes + 53 pendings) it **saturates at
  the 1.0 cap** — so resolving disputes on stage changes nothing on the dashboard.
  That is the most likely live-demo failure.
- **Simulator** (`ai/router.py:216`) never calls the risk engine. It applies a
  *second, different* set of constants, and its level thresholds (0.3/0.6)
  disagree with the engine's (0.20/0.45/0.70). Two models, one label.
- **`/document/analyze` and `/recommendations/{id}`** return hardcoded literals —
  a fixed survey number "124/2", a frozen `generated_at` timestamp, and text that
  ignores `project_id`. `/document/analyze` accepts no file.
- **Local fallback provider** (`provider.py:143-394`) is keyword `if`-matching with
  prose templates. Every `.get()` has a fabricated default (`95.0`, `49`, `53`,
  `80.4%`). Because of P0 #1, **those defaults are what actually renders today.**
  `:352` returns a fully hardcoded 3-project comparison table with `"grounded": true`.
  `:246` invents parcel 100/1 in Chomu, Jaipur, also `grounded: true`.
- Missing Gemini key degrades **silently** — response says `local_fallback` but
  still claims `grounded: true`, and the explanatory `provider_note` is only set
  on the runtime-failure path, never the missing-key path.

**Minimum viable fix (half a day):**
1. Normalise the risk score (log or ratio-based) so it moves in a demo. Show the
   three input counts next to the score — "12 disputes × 0.04 + …" is *defensible*;
   an opaque 93% is not.
2. Make the simulator call the same function as the engine.
3. Set `grounded: false` when you're on the fallback path, and surface a visible
   "AI offline — heuristic mode" chip in the UI. **Honest degradation is a scoring
   criterion on this PS** ("does the system degrade gracefully or just break?").
4. Either make `/document/analyze` accept a real upload and do real OCR, or drop
   it from the demo script. A frozen fake response is worse than an absent feature.

## P2 — Correctness & scale

- `projects/router.py:135` — `compensation_pending` is a **global** count; `parcel_ids`
  is computed and never used. Every project shows the same national number.
- `projects/router.py:140` — `rr_pending` counts all families regardless of status,
  and falls back to `[uuid.uuid4()]` when a project has no parcels.
- `ai/tools.py:130` — `get_compensation_backlog` **ignores its own `project_id`**;
  the copilot's "pending compensation" is always national.
- `ai/tools.py:140` + `analytics/router.py:39` — `pending_amount` sums
  `disbursed_amount` over *pending* rows (money not disbursed). `seed.py:357`
  sets `disbursed_amount` to the full award even for PENDING, so the pending/paid
  split is meaningless. Assessed value should come from `Award.declared_amount`.
- `domain_routers.py:399,403` — GPS check uses `if (lat and lat)` (drops a real
  `0.0`) and Euclidean degrees × 111000 with no `cos(lat)` correction — ~11% error
  at 26°N, so the "100 m" threshold is really ~89 m east-west. Use haversine.
- `projects/router.py:84` — N+1: ~5 queries per project inside the list loop, and
  `list_projects` has **no pagination at all**. Risk filtering happens in Python
  after fetching everything. This is the answer to "how does it hold at production scale?"
- Hardcoded `.limit(100)`/`.limit(50)` with no offset in 6 places.
- `GET /api/ai/risk/{id}` **writes to the DB** (`db.add` + flush, and `get_db`
  commits) — a GET with side effects.
- Status changes travel as **query strings**, not request bodies, in 9 endpoints —
  no schema validation, and they land in access logs.
- Invalid enum strings raise `ValueError` → 500 instead of 400 (4 places).
- `parcels/service.py:70` commits inside the service while `get_db` commits again —
  a partial commit escapes the request-level rollback.
- `database.py:48` — `echo=True` in development logs every SQL statement. Turn it
  off before you demo; the console noise reads as instability.
- Multi-turn copilot memory **never works**: `ai/router.py:115` reads a
  `conversation_id` field that doesn't exist on the schema, so a new UUID is minted
  per request. The session dicts also grow unbounded and are process-local.
- `proposals/service.py:290` — a PROJECT_AGENCY user sees only proposals they
  personally submitted, so a second officer at the same agency sees nothing.

## P2 — Frontend robustness

- **No error boundary anywhere.** One null column blanks a whole page:
  `Projects.tsx:18` (`p.name.toLowerCase()`), `StateDashboard.tsx:108`,
  `Documents.tsx:96,98`, `Analytics.tsx:154`, `Compensation.tsx:27` (→ NaN KPI),
  `Simulator.tsx:151-181`, `ProjectDetail.tsx:41`.
- Errors swallowed to `console.error` on **11 pages** — the user sees an empty
  table and never a message.
- **Expired token leaves you inside the app**: `AuthContext.tsx:32` clears
  localStorage but never `setToken(null)`, so `ProtectedRoute` still renders the
  shell with a null user and fake numbers. And there is **no 401 interceptor** in
  `client.ts` at all.
- **API base URL hardcoded to `localhost:8000`** in *two* places
  (`client.ts:2`, `Map.tsx:7`). No `.env`, no `VITE_*` var. Any build that isn't
  on your laptop shows fallback data everywhere.
- ~12 CSS classes used but never defined (`.form-input`, `.btn-outline`,
  `.btn-success`, `.badge-info/-success/-warning/-error`, `.kpi-header/-title/-footer`)
  — those pages render unstyled inputs and badges.
- **The "mobile field officer portal" is not mobile**: no `navigator.geolocation`
  call at all (lat/lon are text inputs with fixed defaults), no camera/photo upload
  despite the subtitle, a 5-column table in a horizontal scroller, a fixed 540px
  modal, and below 1024px the sidebar collapses to an icon rail with all labels
  `display:none` and no tooltips.
- `Map.tsx` bypasses `client.ts` entirely — its own axios instance, its own token
  reader (which checks a legacy `sih_token` key nothing writes), its own base URL.
- `Map.tsx:210` — `key={JSON.stringify(geoData)}` stringifies the whole
  FeatureCollection on every render. At the claimed 15k parcels this locks the tab.
- Map has no offline/error UI and no `errorTileUrl`; header still says
  "N parcels rendered" after a failed fetch. (Attribution *is* present — fine.)
- **CitizenPortal Hindi is partial**: ~20 inline ternaries, no dictionary. Hectares,
  land types, and all API status values render raw in English (`not_acquired`) in
  Hindi mode; the copilot pins `'en'`; the choice isn't persisted and
  `document.documentElement.lang` never changes.
- 11 buttons ship with **no `onClick`**: "+ New Project", "Export Report",
  "+ File Dispute", "+ Create Task", "+ Upload Document", "Approve", "Review"…
  `api.createProject` exists and is never called. Wire them or hide them.
- Copilot renders `**bold**` as literal asterisks (`BhumiCopilot.tsx:311`).
- `/map` is unreachable from the nav; `/dashboard/state/:x` duplicates `/state/:x`;
  `Layout.tsx:74` hides Field Ops from `central_ministry` while `App.tsx:50` grants it.
- `/citizen` renders outside `<Layout>` — an officer who clicks it in the sidebar
  loses all navigation with no way back but the Back button.

## P3 — Hygiene

- Tailwind is installed and configured but **never used** — no `@import "tailwindcss"`,
  no utility classes anywhere. Delete it, or wire it up.
- `src/App.css` (184 lines of Vite starter) imported by nothing; `react.svg`,
  `vite.svg`, `hero.png` unreferenced.
- `frontend/dist/` and `__pycache__/` are committed to git.
- `index.html` title is literally `frontend`.
- 8 empty backend packages (`disputes/`, `field/`, `compensation/`, `audit/`,
  `workflow/`, `documents/`, `notifications/`) exist with only `__init__.py`, while
  all their code sits in one 605-line `domain_routers.py`. Split it — the current
  layout misleads anyone reading the repo.
- `require_roles()` is a clean RBAC factory used in **exactly one place**; every
  other route hand-rolls `if current_user.role not in (...)`. That's why the two
  ungated endpoints above were missed.
- No tests beyond three ad-hoc `scripts/test_module*.py` HTTP scripts. No CI.
- No Docker / no `docker-compose.yml` — "clone and run" is currently a 10-step
  README. A single `docker compose up` is worth real points on setup-friction.
- Only 1 Alembic migration (`0001_initial_schema`) — everything since has been
  hand-applied. Generate a second revision so the schema is reproducible.
- No structured logging, no request IDs — awkward for a project whose pitch
  centres on an immutable audit trail.

---

## Suggested plan to 20 Sep

**Day 1 (must):** P0 bugs 1-6 + security 7-11. Rotate the leaked DB password and
Gemini key. Turn off SQL echo.

**Day 2-3 (the score):** Kill every hardcoded number in the frontend. Add an
error boundary, a 401 interceptor, and an honest "backend unavailable" state.
Add `VITE_API_URL`.

**Day 4:** AI honesty pass — normalise the risk score, unify the simulator,
`grounded: false` on fallback, show the score's inputs in the UI.

**Day 5:** Real `navigator.geolocation` + photo upload in the field portal
(this is the one feature that most differentiates you from the other 8 teams on
this PS cluster). Finish the Hindi dictionary.

**Day 6:** Docker compose, pagination on `/api/projects`, split `domain_routers.py`,
delete Tailwind and dead assets, fix the README.

**Day 7:** Rehearse the demo with the backend deliberately killed once, to prove
graceful degradation on stage.
