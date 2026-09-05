# BHUMI-AI Frontend — Web Application

> **Intelligent National Land Acquisition & Management Platform**  
> Problem Statement: **SIH26016** · Ministry of Rural Development

The BHUMI-AI frontend is a modern, responsive single-page web application built with **React 19**, **TypeScript**, and **Vite**. It provides administrative dashboards, interactive GIS parcel mapping, statutory acquisition workflows, compensation tracking, dispute monitoring, field verification tools, citizen inquiry services, and conversational AI assistance for land acquisition stakeholders across India.

---

## 🛠️ Frontend Technology Stack

- **Framework**: [React 19](https://react.dev/) (`react@^19.2.8`, `react-dom@^19.2.8`)
- **Language**: [TypeScript](https://www.typescriptlang.org/) (Strict Mode)
- **Build Tool & Bundler**: [Vite 8](https://vitejs.dev/) with Fast HMR
- **Routing**: [React Router DOM v7](https://reactrouter.com/) (`react-router-dom@^7.18.3`)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/) + Custom Semantic Design System in `src/index.css`
  - High-contrast, WCAG AAA compliant navigation styling
  - Responsive 60/40 authentication split layout
  - Accessible government color palette (MoRD Teal `#072F37`, Ministry Blue `#1B6CA8`, Indian Saffron `#E67E22`, Tri-color Green `#27AE60`)
- **GIS & Mapping**: [Leaflet](https://leafletjs.com/) 1.9 & [React-Leaflet](https://react-leaflet.js.org/) 5.0
- **Data Visualization**: [Recharts](https://recharts.org/) 3.10
- **Iconography**: [Lucide React](https://lucide.dev/) (`lucide-react@^1.41.0`)
- **HTTP Client**: Native Typed `fetch` wrapper in `src/api/client.ts`

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: Version `18.0.0` or higher (`node -v`)
- **npm**: Version `9.0.0` or higher (`npm -v`)
- Active BHUMI-AI FastAPI backend server running on `http://localhost:8000`

### 2. Installation

Navigate to the `frontend/` directory and install all required dependencies:

```bash
cd frontend
npm install
```

### 3. Running Development Server

To launch the Vite development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

The application will be accessible at:
```
http://localhost:5173
```
*(Or `http://127.0.0.1:5173`)*

### 4. Building for Production

To perform TypeScript type checking and create an optimized production bundle in `dist/`:

```bash
npm run build
```

To preview the built production bundle locally:

```bash
npm run preview
```

---

## ⚙️ Backend API Configuration & Environment Variables

The frontend communicates with the FastAPI backend through `src/api/client.ts`.

By default, `src/api/client.ts` targets the local FastAPI server:
```typescript
const BASE_URL = 'http://localhost:8000';
```

### Authentication Token Handling
Upon successful login via `POST /auth/login`, the JWT bearer token is stored in the browser's `localStorage` under the key `bhumi_token`. The `request()` helper in `src/api/client.ts` automatically attaches the header:
```http
Authorization: Bearer <bhumi_token>
```
to all authenticated API requests.

---

## 🏛️ Major Frontend Modules & Pages

| Route | Component | Description & Key Features |
|---|---|---|
| `/login` | `Login.tsx` | Responsive 60/40 layout with dark branding hero on left, login form on right, and **1-Click Instant Demo Authentication** cards for 6 statutory roles. |
| `/dashboard` | `Dashboard.tsx` | **National Command Center**: Macro statutory KPIs, active national projects, acquisition phase distribution, and interactive alert feed. |
| `/state/:stateName` | `StateDashboard.tsx` | **State Overview**: State-level rollups (e.g. Rajasthan, Maharashtra), district-wise acquisition breakdown, and state-level approvals. |
| `/projects` | `Projects.tsx` | **Project Directory**: Filterable and searchable catalog of infrastructure projects by ministry, state, and status. |
| `/project/:id` | `ProjectDetail.tsx` | **Project Deep-Dive**: Project summary, statutory lifecycle stages, embedded GIS PostGIS parcel map, compensation awards, disputes, and R&R status. |
| `/compensation` | `Compensation.tsx` | **Compensation & DBT Ledger**: Track assessed land values, solatium (100%), interest, bank disbursement status, and pending approvals. |
| `/disputes` | `Disputes.tsx` | **Legal & Litigation Registry**: Monitor active lawsuits, court stay orders, petitioner claims, and dispute resolution impact on project risk. |
| `/rr` | `RRManagement.tsx` | **Rehabilitation & Resettlement (R&R)**: Entitlement registers for Project-Affected Families (PAF), housing grants, and subsistence packages. |
| `/documents` | `Documents.tsx` | **Document Intelligence**: Section 4/11 gazette notifications, survey reports, sale deeds, and AI-extracted metadata. |
| `/workflow` | `Workflow.tsx` | **Statutory Workflow Tasks**: RFCTLARR statutory task pipeline, priority filters, overdue warnings, and role-based task completion. |
| `/simulator` | `Simulator.tsx` | **What-If Policy Simulator**: Interactive parameter adjustment (compensation multipliers, dispute resolution velocity) to simulate project timeline compression. |
| `/analytics` | `Analytics.tsx` | **Multi-dimensional Analytics**: Interactive charts showing land acquisition throughput, budget burn rates, and regional bottlenecks. |
| `/field` | `FieldDashboard.tsx` | **Field Officer Mobile Portal**: On-ground inspection queue, GPS coordinate validation, boundary checking, and survey photo submissions. |
| `/citizen` | `CitizenPortal.tsx` | **Public Transparency Portal**: Public, unauthenticated search allowing citizens to track acquisition progress and compensation by survey number. |
| `/audit` | `AuditLog.tsx` | **Statutory Audit Log**: Immutable record of all system events, status changes, dispute resolutions, and AI actions. |
| *Bottom-Right* | `Copilot.tsx` | **BHUMI AI Copilot**: Floating conversational assistant providing natural-language analysis grounded in project and parcel database records. |

---

## 🎨 Design System & Accessibility

- **High Contrast Sidebar**: Left navigation items are styled with high-contrast text (`#E2EEF5`) and distinct active states against the `#072F37` background, ensuring zero hover-dependence and full readability.
- **Statutory GIS Colors**: Land parcels on the Leaflet map adhere strictly to standard administrative status colors:
  - 🟢 **Green (`#27AE60`)**: Possessed / Acquired
  - 🟡 **Yellow (`#F1C40F`)**: In Progress (Surveyed)
  - 🟠 **Orange (`#E67E22`)**: Compensation Pending
  - 🔴 **Red (`#E74C3C`)**: Disputed / High Legal Risk
  - 🔵 **Blue (`#2980B9`)**: Statutory Notice Issued (Section 11)
  - ⚪ **Grey (`#95A5A6`)**: Not Started / Proposed
- **Responsive Navigation**: Top navigation includes user profile chip, active role badge, and a functional **System Notification Dropdown** with real-time severity indicators and mark-as-read actions.
