# Smart Dustbin · Knowledge Base & Navigation Index

Welcome to the **Smart Dustbin** project documentation directory. This folder provides a comprehensive, structured index to help developers and AI agents navigate, maintain, debug, and extend both the software stack and the hardware specifications for this project.

---

## 🧭 Document Navigation Map

| Document | Description | Key Topics |
| :--- | :--- | :--- |
| [README.md](file:///f:/smart%20dustbin/md/README.md) | **Master Index & Directory Guide** (this file) | Repository overview, quick file locator, core concepts |
| [ARCHITECTURE.md](file:///f:/smart%20dustbin/md/ARCHITECTURE.md) | **System Architecture & Data Flows** | Dual-loop physical control, backend ingest pipeline, database lifecycle |
| [HARDWARE_AND_PINOUT.md](file:///f:/smart%20dustbin/md/HARDWARE_AND_PINOUT.md) | **Hardware Specifications & Circuit Wiring** | ESP32 GPIO pinout, HC-SR04, SG90, DHT11, I2C LCD, voltage dividers |
| [BACKEND_AND_DATABASE.md](file:///f:/smart%20dustbin/md/BACKEND_AND_DATABASE.md) | **Backend Engine & SQLite Data Store** | `node:sqlite` WAL mode, fill percentage calibration, stable filter, collection detection, ETA estimator |
| [API_REFERENCE.md](file:///f:/smart%20dustbin/md/API_REFERENCE.md) | **REST API Contracts & Endpoints** | Endpoints, payload validation, idempotency via `requestId`, response schemas |
| [FRONTEND_DASHBOARD.md](file:///f:/smart%20dustbin/md/FRONTEND_DASHBOARD.md) | **Client Dashboard Architecture** | Vanilla SPA, hash routing, SVG line chart, modal dialogs, styling system |
| [SYSTEM_REQUIREMENTS_SPEC.md](file:///f:/smart%20dustbin/md/SYSTEM_REQUIREMENTS_SPEC.md) | **SRS & Requirements Traceability Matrix** | Course CSE 4102 specs, UR01–UR08, FR01–FR17, NFR01–NFR10, acceptance tests T01–T12 |
| [DEVELOPER_GUIDE.md](file:///f:/smart%20dustbin/md/DEVELOPER_GUIDE.md) | **Developer Setup, Testing & Operations** | Node 24 requirement, test suites (`node --test`), launch scripts, troubleshooting |

---

## 📁 Repository Structure

```text
f:/smart dustbin/
├── package.json                         # Root project scripts (start, test)
├── package-lock.json
│
├── dashboard/                           # Production Collector Dashboard application
│   ├── package.json                     # Node.js project file (type: module, engines: node >= 24)
│   ├── server.js                        # Express HTTP server & simulation tick runner
│   ├── store.js                         # SQLite data layer, calibration, collection & ETA rules
│   ├── launch.js                        # Idempotent dashboard launcher (checks if already running)
│   ├── Start Dashboard.cmd              # Windows double-click startup batch script
│   ├── README.md                        # Quick demonstration guide
│   ├── smartbin.db                      # SQLite WAL database file
│   │
│   ├── public/                          # Frontend browser assets (no build step required)
│   │   ├── index.html                   # Dashboard markup, templates, dialog modals
│   │   ├── app.js                       # Vanilla ES6 client application, routing, SVG charts
│   │   ├── style.css                    # Design system, variables, responsive layout
│   │   └── fonts/                       # Locally bundled webfonts (Manrope & Space Grotesk)
│   │
│   └── test/
│       └── store.test.js                # Built-in Node test suite (bounds, collection, idempotency, etc.)
│
├── output/                              # Formal Academic Deliverables
│   ├── latex/
│   │   └── Smart_Dustbin_SRS.tex        # LaTeX IEEE/academic SRS specification
│   └── pdf/
│       └── Smart_Dustbin_SRS.pdf        # Compiled SRS document (Bangladesh University of Professionals)
│
├── tmp/                                 # Build tools & historical assets
│   └── pdfs/
│       ├── build_srs.py                 # ReportLab python script for generating SRS PDF
│       ├── make_latex.py                # Ast parser translating python script into LaTeX
│       └── revise_open_srs.py           # AST patcher adjusting LaTeX report contents
│
└── md/                                  # 📍 THIS DOCUMENTATION FOLDER
    ├── README.md                        # Master Index (You are here)
    ├── ARCHITECTURE.md                  # High-level architecture and subsystem interactions
    ├── HARDWARE_AND_PINOUT.md           # Pinouts, circuits, electrical requirements
    ├── BACKEND_AND_DATABASE.md          # Server logic, data calculations, SQLite schema
    ├── API_REFERENCE.md                 # Complete API documentation
    ├── FRONTEND_DASHBOARD.md            # Frontend UI architecture and design system
    ├── SYSTEM_REQUIREMENTS_SPEC.md      # Formal system requirements specification
    └── DEVELOPER_GUIDE.md               # Quickstart, testing, and operations
```

---

## ⚡ Quick Reference

### Running the System
```powershell
# From workspace root:
npm start

# Or directly from the dashboard directory:
cd dashboard
npm start

# Running tests:
npm test
```

- **Dashboard URL**: `http://localhost:3000`
- **Default Port**: `3000` (configurable via `PORT` environment variable)
- **Runtime Requirement**: Node.js **24.0.0+** (uses built-in `node:sqlite`)
- **Timezone**: `Asia/Dhaka` (UTC+6)
- **Primary Data File**: [`dashboard/smartbin.db`](file:///f:/smart%20dustbin/dashboard/smartbin.db)
