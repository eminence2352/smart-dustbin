# Developer Guide & Operations

This guide provides instructions for developers and maintainers working with the **Smart Dustbin** codebase. It covers local setup, running tests, database inspection, connecting physical hardware, and troubleshooting.

---

## 1. Prerequisites

- **Node.js**: Version **24.0.0 or newer** is required to support the native `node:sqlite` module without third-party native compilation.
  ```powershell
  node --version  # Must output v24.x.x or higher
  ```
- **Operating System**: Windows, macOS, or Linux. (Batch scripts like [`Start Dashboard.cmd`](file:///f:/smart%20dustbin/dashboard/Start%20Dashboard.cmd) are designed for Windows).
- **Network**: Local Wi-Fi router or mobile hotspot on $2.4\text{ GHz}$ for hardware connectivity.

---

## 2. Installation & Quickstart

### Step 1: Install Dependencies
```powershell
# From workspace root:
cd "f:\smart dustbin\dashboard"
npm install
```

### Step 2: Start the Server
You have three options:

1. **Via Workspace Root**:
   ```powershell
   npm start
   ```
2. **Via Dashboard Folder**:
   ```powershell
   cd dashboard
   npm start
   ```
3. **Via Windows Batch Script**:
   Double-click [`dashboard/Start Dashboard.cmd`](file:///f:/smart%20dustbin/dashboard/Start%20Dashboard.cmd).

Open **http://localhost:3000** in your web browser.

---

## 3. Running Unit Tests

The test suite uses Node.js's built-in test runner (`node:test`) and strict assertions (`node:assert/strict`).

```powershell
# Run tests from root:
npm test

# Or run directly inside the dashboard directory:
node --test test/store.test.js
```

### Test Coverage Summary:
- **`calibration and bounds`**: Verifies distance-to-percent math ($19\text{ cm} \rightarrow 60\%$, $45\text{ cm} \rightarrow 0\%$, $2\text{ cm} \rightarrow 100\%$, $\text{null} \rightarrow \text{null}$).
- **`stable collection occurs once; single outlier does not collect`**: Validates the 3-reading filter and hysteresis drop from $\ge 70\%$ to $\le 10\%$.
- **`null sensors retain last fill but still count openings; duplicate batches are idempotent`**: Validates fault tolerance when sensors return null, as well as `requestId` deduplication.
- **`manual collection clears high window and does not fabricate empty fill`**: Verifies manual resets without faking $0\%$ fill.
- **`offline and prediction data requirements`**: Validates the 30-second offline threshold and the 10-minute linear projection ETA formula.
- **`invalid data does not mutate state`**: Confirms that out-of-range inputs throw HTTP 400 errors without altering database records.
- **`SQLite state survives reopening`**: Validates disk persistence using temporary databases.
- **`HTTP reading pipeline validates and serves locally bundled assets`**: End-to-end integration test verifying static assets, font files, and API routes.

---

## 4. Database Management & Inspection

The database file is located at:
`f:/smart dustbin/dashboard/smartbin.db`

### Quick Inspection using Node.js:
Run this quick snippet in PowerShell to inspect the database:
```powershell
node -e "const { DatabaseSync } = require('node:sqlite'); const db = new DatabaseSync('dashboard/smartbin.db'); console.log(db.prepare('SELECT id, data FROM bins').all().map(r => JSON.parse(r.data)));"
```

### Resetting to Default Seed Data:
To reset the database back to its fresh state:
1. Stop the dashboard server.
2. Delete the database files in `dashboard/`:
   ```powershell
   Remove-Item dashboard/smartbin.db*
   ```
3. Restart the server (`npm start`). The store will automatically re-seed 6 campus locations with fresh sample historical trends.

---

## 5. Integrating the Physical ESP32 Hardware

To hook up the real physical ESP32 bin to the dashboard:

1. **Find the Host Computer's Local IP Address**:
   ```powershell
   ipconfig
   # Look for IPv4 Address on your Wi-Fi adapter (e.g. 192.168.1.15)
   ```
2. **Allow Inbound Connections on Port 3000**:
   Ensure Windows Defender Firewall allows incoming connections on port `3000` for your local private network.
3. **Configure ESP32 Firmware**:
   - Set the Wi-Fi SSID and password to match your local network.
   - Set the target server endpoint:
     ```c
     const char* serverUrl = "http://192.168.1.15:3000/api/readings";
     ```
   - Set `binId` to one of the registered IDs (e.g., `"bin-01"`).
4. **Ingestion Loop in Firmware**:
   - Package JSON payload:
     ```json
     {
       "binId": "bin-01",
       "distanceCm": 18.5,
       "tempC": 28.2,
       "humidity": 65.0,
       "opensDelta": 1,
       "requestId": "device-uuid-here"
     }
     ```
   - Send via `HTTPClient` with header `Content-Type: application/json`.
   - On response, parse `fill` and display on the 16x2 I2C LCD screen.

---

## 6. Troubleshooting Common Issues

### Issue 1: "ExperimentalWarning: SQLite is an experimental feature"
- **Cause**: Node.js displays this warning when using `node:sqlite`.
- **Action**: This is normal and expected. It does not affect execution or stability.

### Issue 2: "Smart Dustbin is already running. Open http://localhost:3000"
- **Cause**: [`launch.js`](file:///f:/smart%20dustbin/dashboard/launch.js) pings port 3000 before spawning a new server to prevent conflicting port crashes.
- **Action**: An instance is already running. Open your browser to the URL or stop the running process if you wish to restart.

### Issue 3: Port 3000 Already In Use by Another Application
- **Action**: Launch on a custom port using the `PORT` environment variable:
  ```powershell
  $env:PORT = "4000"; npm start
  ```

### Issue 4: ESP32 Resets When Lid Opens
- **Cause**: The SG90 servo is drawing peak current from the ESP32's onboard 3.3V pin, causing an electrical brownout.
- **Solution**: Connect the servo power wire (Red) directly to an external 5V power supply, connect all GND lines together, and solder a 100µF capacitor across the 5V power rail.
