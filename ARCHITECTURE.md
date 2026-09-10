# ARCHITECTURE.md: System Specification

## 1. Storage Subsystems & Relational Schemas
The core relational model maps directly to the offline-first IndexedDB instance and the server-side SQLite store. Total volume is strictly constrained to <1000 Tune records[cite: 2].

### 1.1 Event Schema
Setlists are strictly 1:1 with Events, permanently eliminating independent Setlist entities and referential orphan states[cite: 2].
* `id`: UUID PRIMARY KEY
* `name`: TEXT NOT NULL
* `date`: TEXT NOT NULL (ISO 8601)
* `description`: TEXT
* `tune_ids`: TEXT NOT NULL (JSON Array of Tune UUIDs)[cite: 2]
* `updated_at`: INTEGER NOT NULL (Unix epoch ms)
* `deleted_at`: INTEGER NULL (Tombstone for LWW sync)[cite: 2]

### 1.2 Tune Schema
Variants are instantiated as distinct, independent entities with no inheritance trees[cite: 2].
* `id`: UUID PRIMARY KEY
* `primary_title`: TEXT NOT NULL
* `alternate_titles`: TEXT (JSON Array of strings)
* `media_hash`: TEXT NOT NULL (SHA-256 CAS digest)[cite: 2]
* `media_type`: TEXT NOT NULL ('PDF', 'IMAGE', 'SVG')
* `transform_data`: TEXT (JSON: `{ rotation: INT, crop_rect: [x,y,w,h] }`)
* `annotation_data`: TEXT (JSON Vector definitions)
* `updated_at`: INTEGER NOT NULL
* `deleted_at`: INTEGER NULL (Tombstone)[cite: 2]

## 2. Media Storage Strategy (CAS)
Media blobs are immutable binary payloads decoupled from lightweight relational sync[cite: 2].
* **Mechanism:** Addressed exclusively by SHA-256 digest[cite: 2].
* **Transport:** CAS endpoints handle decoupled media up/downloads independent of the JSON entity push/pull[cite: 2].

## 3. Frontend Subsystems & State Machines
* **Screen Wake Lock:** Acquired explicitly upon entering Performance View to suppress the device sleep timer; released upon exit or visibility loss[cite: 2].
* **Navigation & Input:** Swiping gestures for navigation are strictly isolated from annotation rendering[cite: 2].
* **Setlist Assembly:** Utilizes text-based fuzzy matching against `primary_title` and `alternate_titles` with instant visual feedback[cite: 2].

### 3.1 Annotation Engine
* **Coordinates:** Strokes are stored as normalized coordinates (0.0 to 1.0) to maintain resolution independence[cite: 2].
* **Modes:** Explicit UI toggle state machine between "Draw" and "Lasso"[cite: 2].
* **Selection:** Lasso mode utilizes ray-casting on a closed polygon to select stroke centroids for moving or deleting[cite: 2].
* **State:** Session-level undo/redo stack[cite: 2].

### 3.2 State-Lock Enforcement
* Crop and rotate operations are permanently hard-disabled for a Tune once `annotation_data` is non-null[cite: 2].

## 4. Data Ingestion & Media Pipeline
* **Source:** Import via public ABC sites, email attachments, and device camera[cite: 2].
* **PDF Truncation:** Multi-page PDFs are strictly truncated; only Page 1 is extracted and saved, with subsequent pages dropped[cite: 2].
* **ABC Rendering:** ABC notation is rendered to a static image/SVG at ingestion to guarantee a uniform visual pipeline[cite: 2].
* **Transformations:** Image crop and rotate tools are non-destructive and mapped via CSS/Canvas transforms[cite: 2].

## 5. Synchronization Protocol
* **Topology:** Authenticated sync to a self-hosted web backend supporting multiple devices per account[cite: 2].
* **Conflict Resolution:** Unconditional Last-Write-Wins (LWW) at the entity level utilizing `updated_at` timestamps and `deleted_at` tombstones[cite: 2].
* **Exclusions:** Delta-based sync conflict resolution and backend database backups are explicitly out of scope[cite: 2].

## 6. Project Directory Layout & Technology Stack

### 6.1 Stack
* **Backend:** Python 3.11+, FastAPI, SQLite. Minimal dependencies.
* **Frontend:** Preact, JSX, HTML5, CSS3. IndexedDB wrapper (Dexie.js). PDF.js for ingestion.

### 6.2 Directory Structure
/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── models.py        # SQLite schemas / Pydantic models
│   │   ├── sync.py          # LWW sync logic
│   │   └── cas.py           # Content-addressable storage logic
│   ├── data/                # SQLite DB and Media files
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── vite.config.js       # Preact compilation
│   ├── src/
│   │   ├── app.jsx          # Init & Routing
│   │   ├── db.js            # IndexedDB schema & access
│   │   ├── sync.js          # Client-side sync client
│   │   ├── EventView.jsx
│   │   ├── PerformanceView.jsx
│   │   ├── AnnotationEngine.js # Canvas draw/lasso logic
│   │   └── ingest.js        # PDF/ABC parsing & CAS hashing
│   └── tests/
└── ARCHITECTURE.md
