# REST API Reference

The **Smart Dustbin** backend exposes a lightweight, JSON-based RESTful API running by default on port `3000`. All endpoints under `/api` include `Cache-Control: no-store` headers to ensure fresh data delivery.

---

## 1. Summary of Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | [`/api/bins`](#1-get-apibins) | List all registered bins with live status, fill %, and server time |
| `GET` | [`/api/bins/:id`](#2-get-apibinsid) | Get detailed status, recent readings, and collection history for one bin |
| `GET` | [`/api/bins/:id/readings`](#3-get-apibinsidreadings) | Get time-series readings for a bin with optional limit parameter |
| `GET` | [`/api/bins/:id/collections`](#4-get-apibinsidcollections) | Get collection history specific to one bin |
| `GET` | [`/api/collections`](#5-get-apicollections) | Get global collection history across all campus bins |
| `POST`| [`/api/readings`](#6-post-apireadings) | Ingest a new sensor reading batch (physical ESP32 or simulator) |
| `POST`| [`/api/bins/:id/collect`](#7-post-apibinsidcollect) | Record a manual collection event for a specific bin |
| `POST`| [`/api/demo/simulation`](#8-post-apidemosimulation) | Global toggle to pause or resume background simulation |
| `POST`| [`/api/demo/bins/:id`](#9-post-apidemobinsid) | Individual toggle to pause or resume simulation for a single bin |

---

## 2. Ingestion & Core Endpoints

### 1. `GET /api/bins`
Returns all registered bins with current computed state.

#### Response (`200 OK`)
```json
{
  "bins": [
    {
      "id": "bin-01",
      "name": "Central courtyard",
      "address": "Main courtyard, ground floor",
      "emptyDistance": 40,
      "fullDistance": 5,
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
      "online": true,
      "estimate": {
        "label": "Estimated collection",
        "at": 1728339400000
      },
      "source": "simulated",
      "paused": false
    }
  ],
  "running": true,
  "serverTime": 1728331205123
}
```

---

### 2. `GET /api/bins/:id`
Retrieves single bin details along with its reading history and collection records.

#### Example Request
```bash
curl http://localhost:3000/api/bins/bin-01
```

#### Response (`200 OK`)
```json
{
  "id": "bin-01",
  "name": "Central courtyard",
  "address": "Main courtyard, ground floor",
  "fill": 72.4,
  "online": true,
  "valid": true,
  "readings": [
    { "ts": 1728329400000, "fill": 68.2 },
    { "ts": 1728331200000, "fill": 72.4 }
  ],
  "collections": [
    {
      "id": 1,
      "bin_id": "bin-01",
      "ts": 1728320400000,
      "method": "sample"
    }
  ]
}
```

#### Error Response (`404 Not Found`)
```json
{ "error": "Bin not found." }
```

---

### 3. `GET /api/bins/:id/readings`
Returns chronological reading points for charting.

#### Query Parameters:
- `limit` (optional, integer, default: `200`, range: `1` to `500`): Maximum data points to return.

#### Example Request
```bash
curl "http://localhost:3000/api/bins/bin-01/readings?limit=50"
```

#### Response (`200 OK`)
```json
[
  { "ts": 1728325000000, "fill": 55.4 },
  { "ts": 1728326800000, "fill": 58.1 }
]
```

---

### 4. `GET /api/bins/:id/collections`
Returns the collection history for a specific bin.

#### Response (`200 OK`)
```json
[
  { "id": 4, "bin_id": "bin-01", "ts": 1728320400000, "method": "manual" }
]
```

---

### 5. `GET /api/collections`
Returns the recent collection history across all campus bins (limit 100).

#### Response (`200 OK`)
```json
[
  { "id": 12, "bin_id": "bin-02", "ts": 1728330000000, "method": "auto" },
  { "id": 11, "bin_id": "bin-01", "ts": 1728320400000, "method": "manual" }
]
```

---

### 6. `POST /api/readings`
Ingests a new telemetry batch. Used by both the physical ESP32 firmware and the browser demo simulator.

#### Request Headers:
`Content-Type: application/json`

#### Request Payload:
```json
{
  "binId": "bin-01",
  "distanceCm": 13.75,
  "tempC": 28.5,
  "humidity": 62.0,
  "opensDelta": 1,
  "requestId": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Validation Constraints:
| Field | Type | Rules |
| :--- | :--- | :--- |
| `binId` | `string` | Must match an existing registered bin. |
| `distanceCm` | `number \| null` | Nullable. If provided: $0.01 \le \text{distance} \le 400.0$ cm. |
| `tempC` | `number \| null` | Nullable. If provided: $0.0 \le \text{temp} \le 50.0$ °C. |
| `humidity` | `number \| null` | Nullable. If provided: $0.0 \le \text{humidity} \le 100.0$ %. |
| `opensDelta` | `integer` | Safe integer: $0 \le \text{opensDelta} \le 10,000$. |
| `requestId` | `string` (optional) | String identifier (max length 100) for idempotent deduplication. |

#### Successful Ingestion (`200 OK`)
```json
{
  "ok": true,
  "collected": false,
  "fill": 75.0
}
```

#### Deduplicated Ingestion (`200 OK`)
```json
{
  "ok": true,
  "duplicate": true
}
```

#### Error Responses
- **400 Bad Request**:
  ```json
  { "error": "distanceCm must be 0.01 to 400, or null." }
  ```
- **404 Not Found**:
  ```json
  { "error": "Bin not found." }
  ```

---

### 7. `POST /api/bins/:id/collect`
Manually records a collection event for a bin when emptied by staff.

#### Request Payload:
```json
{
  "requestId": "manual-action-uuid-12345"
}
```

#### Response (`200 OK`)
```json
{
  "ok": true
}
```

---

## 3. Demo & Simulation Control Endpoints

### 8. `POST /api/demo/simulation`
Toggles the global background simulation ticker.

#### Request Payload:
```json
{ "running": false }
```

#### Response (`200 OK`)
```json
{ "running": false }
```

---

### 9. `POST /api/demo/bins/:id`
Pauses or resumes automatic simulation updates for a specific bin.

#### Request Payload:
```json
{ "paused": true }
```

#### Response (`200 OK`)
```json
{ "ok": true }
```
