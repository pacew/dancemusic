# Product Requirements Document (PRD)

## 1. Vision & Core Workflows
* **Target User:** Social dance musicians, specifically English Country Dance[cite: 1].
* **Core Workflow:** Displaying single-page lead sheets on a tablet on a music stand during live performances[cite: 1].
* **Operating Environment:** Live performance venues with presumed zero network connectivity[cite: 1].

## 2. Core Entities & Data Models
* **Event:** `id`, `name`, `date`, `description`, `tune_ids` (JSON Array), `updated_at`, `deleted_at` (Tombstone)[cite: 2].
  * *Invariant:* Setlists are strictly 1:1 with Events; there is no independent Setlist entity[cite: 2].
* **Tune:** `id`, `primary_title`, `alternate_titles`, `media_hash` (CAS SHA-256), `media_type`, `transform_data` (crop/rotate JSON), `annotation_data`, `updated_at`, `deleted_at`[cite: 2].
  * *Invariant:* Limit: <1000 records[cite: 1]. Variants are instantiated as distinct, independent `Tune` entities.
* **Media Blob (CAS):** Immutable binary payloads (PDF, Image, SVG) stored via SHA-256 digest to decouple large files from lightweight relational sync[cite: 2].

## 3. Functional Requirements
* **Ingestion:** Import via public ABC sites, email attachments, and device camera[cite: 1].
  * *Constraint:* Multi-page PDFs are strictly truncated at ingestion; only Page 1 is extracted and saved[cite: 2].
  * *Constraint:* ABC notation is rendered to a static image/SVG at the time of ingestion to ensure a uniform visual rendering pipeline[cite: 2].
* **Library Management:** Non-destructive image crop and rotate tools mapped via CSS/Canvas transforms[cite: 2].
  * *Constraint:* Crop and rotate operations are permanently hard-disabled for a `Tune` once `annotation_data` is non-null[cite: 2].
* **Event View:** Left column lists Events sorted by date descending. Right column displays Event details and a scrollable, reorderable setlist[cite: 1].
* **Setlist Assembly:** Text-based fuzzy matching against `primary_title` and `alternate_titles`[cite: 1]. Instant visual feedback during string input[cite: 1].
* **Performance View:** Minimal UI rendering the lead sheet and system status bar, with a Back button[cite: 1].
* **Annotation Engine:** Touch-based vector drawing with selectable colors[cite: 1].
  * *Tooling:* Explicit UI toggle between "Draw" and "Lasso" modes. Lasso uses ray-casting on a closed polygon to select stroke centroids for moving/deleting[cite: 2].
  * *Data:* Strokes are stored as normalized coordinates (0.0 to 1.0) to maintain resolution independence[cite: 2].
  * *State:* Session-level undo/redo stack[cite: 2].
* **Synchronization:** Authenticated sync to a self-hosted web backend supporting multiple devices per account[cite: 1].
  * *Protocol:* Unconditional Last-Write-Wins (LWW) at the entity level utilizing `updated_at` and `deleted_at` tombstones[cite: 2]. CAS is used for decoupled media up/downloads[cite: 2].

## 4. Explicit Non-Goals / Out of Scope
* Paginating or rendering multi-page tunes[cite: 1].
* Exporting photos or PDFs[cite: 1].
* Search indexing beyond tune titles[cite: 1].
* Event list filtering or search[cite: 1].
* Delta-based sync conflict resolution[cite: 1].
* Backend database backups[cite: 1].

## 5. UI/UX Ergonomics & State Invariants
* **Hardware State:** Screen Wake Lock API is explicitly acquired upon entering Performance View and released upon exit or visibility loss[cite: 2].
* **Input State:** Swiping gestures for navigation must be strictly isolated from annotation rendering[cite: 1].
* **Design Language:** Simple, functional, non-innovative[cite: 1].

## 6. Verification & Acceptance Invariants
* **V1:** Attempting to crop/rotate a tune with existing annotations throws a disabled state UI.
* **V2:** A multi-page PDF imported into the system results in a single-page media asset; subsequent pages are dropped silently or with a single warning alert.
* **V3:** Connecting two devices with divergent offline edits to the same Event results in a clean overwrite based on the latest timestamp (including deletions via tombstone), without application crash.
* **V4:** Selecting a tune from the setlist immediately suppresses the device sleep timer; navigating back to the Event View restores the default OS sleep timer.

