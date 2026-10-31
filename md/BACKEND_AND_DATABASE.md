# Backend Engine & SQLite Data Store

This document explains the server-side implementation located in [`dashboard/server.js`](file:///f:/smart%20dustbin/dashboard/server.js) and [`dashboard/store.js`](file:///f:/smart%20dustbin/dashboard/store.js), covering the Node.js 24 native SQLite storage layer, calculation models, collection detection, and the linear projection algorithm.

---

## 1. Node.js 24 Native SQLite Architecture

The system uses the built-in `node:sqlite` module (`DatabaseSync`), introduced natively in Node.js 22.5+ and standard in Node.js 24+. 

### Advantages:
- **Zero Native Build Dependencies**: No need for `node-gyp`, Visual Studio C++ build tools, or Python on Windows.
- **WAL Mode (`PRAGMA journal_mode=WAL`)**: Write-Ahead Logging allows concurrent readers to query bin state without locking the database file during writes.
- **Synchronous In-Process API**: Provides simple, robust ACID transactional safety without Promise overhead for SQLite operations.

---

## 2. Database Schema

The database file is located at [`dashboard/smartbin.db`](file:///f:/smart%20dustbin/dashboard/smartbin.db). Four core tables are created automatically on launch:

```sql
PRAGMA journal_mode = WAL;

-- Bins table: Primary metadata and working state serialized as JSON
CREATE TABLE IF NOT EXISTS bins (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);

-- Readings table: Time-series log of all ingested sensor readings
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY,
    bin_id TEXT NOT NULL,
    ts INTEGER NOT NULL,
    fill REAL,
    stable REAL,
    distance REAL,
    temp REAL,
    humidity REAL
);
CREATE INDEX IF NOT EXISTS readings_bin_ts ON readings(bin_id, ts);

-- Collections table: Log of all emptied events (automatic, manual, or sample seed)
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY,
    bin_id TEXT NOT NULL,
    ts INTEGER NOT NULL,
    method TEXT NOT NULL  -- 'auto', 'manual', or 'sample'
);

-- Requests table: Deduplication store for idempotent retry protection
CREATE TABLE IF NOT EXISTS requests (
    key TEXT PRIMARY KEY
);
```

### JSON Data Schema for `bins`
The `bins.data` column stores the following JSON object structure:

```json
{
  "id": "bin-01",
  "name": "Central courtyard",
  "address": "Main courtyard, ground floor",
  "emptyDistance": 40.0,
  "fullDistance": 5.0,
  "highThreshold": 70,
  "lowThreshold": 10,
  "target": 90,
  "lastCollectedAt": 1728320400000,
  "usesSinceCollection": 14,
  "lastSeenAt": 1728331200000,
  "fill": 72.4,
  "fillAt": 1728331200000,
  "tempC": 28.6,
  "humidity": 61,
  "distanceCm": 14.66,
  "valid": true,
  "window": [71.8, 72.1, 72.4],
  "lastStable": 72.1,
  "baseline": 12.0,
  "baselineAt": 1728321000000,
  "paused": false
}
```

---

## 3. Core Algorithms & Logic

### 3.1 Fill Percentage Calculation
Implemented via `fillPercent(d, empty = 40, full = 5)`:

$$\text{fill} = \operatorname{clamp}\left(0, 100, \frac{\text{empty} - d}{\text{empty} - \text{full}} \times 100\right)$$

- Clamped between $0\%$ and $100\%$ and rounded to 1 decimal place.
- If $d = \text{null}$ (sensor reading failed or lid was open), returns `null`.
- **Fault-Tolerance**: If distance is null, the bin keeps its **last known fill level**, sets `valid = false`, but continues processing valid temperature, humidity, and lid opening counts ([FR10](file:///f:/smart%20dustbin/md/SYSTEM_REQUIREMENTS_SPEC.md#fr10-fill-calculation-and-partial-fault-tolerance)).

### 3.2 Stability Filtering Window
Single ultrasonic readings are susceptible to turbulence, paper bag peaks, or irregular trash placement. 

1. Up to 3 consecutive valid fill readings are pushed into `b.window`:
   ```javascript
   b.window.push(fill);
   b.window = b.window.slice(-3);
   ```
2. When `window.length === 3` and the difference between maximum and minimum values is $\le 5\%$:
   ```javascript
   if (b.window.length === 3 && Math.max(...b.window) - Math.min(...b.window) <= 5) {
     stable = [...b.window].sort((a, b) => a - b)[1]; // Median
   }
   ```
3. The median value represents the current **stable fill**.

### 3.3 Automatic Collection Detection
The backend continuously looks for a major drop in stable waste height:

```mermaid
flowchart TD
    W[New Stable Median Computed] --> CHK{lastStable >= 70% AND\ncurrent stable <= 10%?}
    CHK -- Yes --> AUTO[Trigger Automatic Collection]
    AUTO --> INS[INSERT INTO collections\nmethod='auto']
    AUTO --> RST[Reset usesSinceCollection = 0\nlastCollectedAt = now\nwindow = []\nlastStable = null\nbaseline = null]
    CHK -- No --> UPD[Update lastStable = current stable]
    UPD --> BL{lastCollectedAt exists AND\nbaseline == null?}
    BL -- Yes --> SETBL[Set baseline = stable\nbaselineAt = now]
    BL -- No --> DONE[Proceed to Ingest Completion]
```

- **Hysteresis Guarantee**: Once emptied ($<10\%$), further readings at $6\%$ or $8\%$ will **not** trigger repeated collections, because `lastStable` is no longer $\ge 70\%$.

### 3.4 Manual Collection Reset
When facilities staff manually empty a bin that did not register automatic collection (e.g. emptied when only 50% full):
- Triggered by `POST /api/bins/:id/collect`.
- Inserts record into `collections` with `method = 'manual'`.
- Resets `usesSinceCollection = 0` and `lastCollectedAt = now`.
- Clears the sliding window and baseline.
- **Does NOT invent a 0% fill reading**: Retains the actual physical reading until a new stable reading arrives.

### 3.5 Linear Fill Rate & Estimated Time of Arrival (ETA)
In `store.view(b, now)`:
1. If $b.\text{fill} \ge 90\%$, returns label: **"Collect now"**.
2. If the bin is currently offline ($>30\text{ s}$ without reading), returns: **"Offline · last known data"**.
3. If $b.\text{baselineAt}$ exists and $\ge 10\text{ minutes}$ have elapsed:
   - Fetches all historical stable points since `baselineAt`:
     ```sql
     SELECT ts, stable FROM readings 
     WHERE bin_id = ? AND ts >= ? AND stable IS NOT NULL 
     ORDER BY ts ASC
     ```
   - Checks prerequisites:
     - At least **5 stable data points** recorded.
     - Elapsed duration $\ge 600,000\text{ ms}$ (10 minutes).
     - Fill velocity is strictly positive ($\text{rate} > 0$):
       $$\text{rate} = \frac{\text{last.stable} - \text{baseline}}{\text{elapsed}}$$
   - Projects estimated target arrival time:
     $$\text{ETA} = \text{last.ts} + \frac{\text{target} - \text{last.stable}}{\text{rate}}$$
4. If prerequisites are not met, cleanly displays: **"Not enough data yet"**.

---

## 4. Idempotency & Network Retry Safety

To prevent duplicate opening counts when the ESP32 retries an HTTP POST whose ACK was dropped:
- Ingestion endpoints accept an optional `requestId` string.
- The server checks `requests` table for key `${binId}:${requestId}`:
  ```javascript
  const key = p.requestId ? `${b.id}:${p.requestId}` : null;
  if (key && db.prepare('SELECT key FROM requests WHERE key=?').get(key)) {
    return { ok: true, duplicate: true };
  }
  ```
- If the key was previously processed, the server skips mutating state and returns `{ ok: true, duplicate: true }`.

---

## 5. Background Simulation Runner

When launched directly (`node server.js`), `server.js` maintains an active ticker running every 5 seconds:
- Simulates realistic fill increments across campus bins.
- When fill reaches $\ge 99\%$, drops to $6\%$ to demonstrate automatic collection transitions.
- Individual bins can be paused or resumed via the demo controls.
