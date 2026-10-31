# Smart Dustbin · IoT Waste Management System

An end-to-end Smart Dustbin IoT system featuring a dual-loop responsive microcontroller architecture (ESP32 / ESP8266) and a real-time web telemetry dashboard powered by Node.js, Express, and SQLite WAL mode.

---

## 📋 System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    PHYSICAL DUSTBIN                     │
│  [IR Proximity Sensor] ──> Smooth Servo Motor (Lid)     │  <-- Local Edge Loop
│  [HC-SR04 Ultrasonic]  ──> Bin Fill Level               │      (<15ms instant response)
│  [DHT11 Sensor]        ──> Ambient Temp & Humidity      │
│  [16x2 I2C LCD]        ──> Real-time Local Status       │
└───────────────────────────┬─────────────────────────────┘
                            │ Wi-Fi (HTTP POST /api/readings)
                            ▼
┌─────────────────────────────────────────────────────────┐
│               COLLECTOR DASHBOARD SERVER                │
│  Node.js 24 + Express 5 + SQLite (WAL Mode)             │  <-- Cloud / LAN Server
│  - Multi-reading Stable Fill Filtering (Median Filter)  │      (Zero setup, built-in DB)
│  - Automatic Collection & Emptying Detection            │
│  - Predictive Time-to-Fill Estimation (Linear Trend)    │
│  - Responsive SPA Dashboard (No build step required)    │
└─────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Setup Guide (For Collaborators & Friends)

### 1. Prerequisites

Before starting, make sure you have the following installed on your computer:

1. **Node.js 24.0.0 or higher**:
   - **Crucial**: This project uses Node's built-in `node:sqlite` (`DatabaseSync`), which removes the need for `python`, `node-gyp`, or Visual Studio C++ compilers on Windows!
   - Verify your version in terminal:
     ```bash
     node -v
     # Must output v24.x.x or higher
     ```
   - Download from: [https://nodejs.org](https://nodejs.org)

2. **Arduino IDE 2.x**:
   - Download from: [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software)

---

### 2. Dashboard & Server Setup

1. **Clone the repository**:
   ```bash
   git clone <REPO_URL>
   cd smart-dustbin
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```
   *(This automatically installs Express and locally bundled font assets inside `dashboard/`)*.

3. **Start the Dashboard**:
   ```bash
   npm start
   ```
   *Alternatively on Windows, you can simply double-click `dashboard/Start Dashboard.cmd`.*

4. **Open in browser**:
   - Navigate to: **`http://localhost:3000`**
   - The dashboard comes preloaded with simulated campus bins and history.

5. **Run test suite**:
   ```bash
   npm test
   ```
   *Runs built-in tests verifying calibration bounds, collection detection, idempotency, and SQLite persistence.*

---

### 3. Hardware Wiring & Pinout

You can use either an **ESP32** (recommended) or a **NodeMCU ESP8266**.

#### Pin Mapping Table

| Component | Pin Function | ESP32 Pin | ESP8266 (NodeMCU) Pin | Wiring Notes |
| :--- | :--- | :--- | :--- | :--- |
| **IR Obstacle Sensor** | Signal (OUT) | `GPIO 27` | `D6` (GPIO 12) | Active LOW (hand detection) |
| **Servo Motor (SG90)** | PWM Signal | `GPIO 13` | `D7` (GPIO 13) | Connect VCC to 5V external power |
| **DHT11 Sensor** | Data Signal | `GPIO 4` | `D5` (GPIO 14) | Temperature & Humidity |
| **Ultrasonic HC-SR04** | Trigger (Trig) | `GPIO 23` | `D0` (GPIO 16) | Distance trigger pulse |
| **Ultrasonic HC-SR04** | Echo (Echo) | `GPIO 18` | `D8` (GPIO 15) | Use voltage divider (5V to 3.3V) |
| **16x2 I2C LCD** | SDA | `GPIO 21` | `D2` (GPIO 4) | I2C Data line |
| **16x2 I2C LCD** | SCL | `GPIO 22` | `D1` (GPIO 5) | I2C Clock line |

> [!IMPORTANT]
> **Power Supply & Common Ground**: Servos draw peak currents up to 500mA–1A during motion. Power your servo and sensors from a dedicated 5V power supply or USB power rail. **Always connect the Ground (GND) of the external power supply to the GND pin of the ESP board.**

---

### 4. Firmware Configuration & Flashing

1. **Open Arduino IDE** and open the firmware file:
   `firmware/smart_dustbin/smart_dustbin.ino`

2. **Install Required Arduino Libraries**:
   Go to **Tools** -> **Manage Libraries...** (`Ctrl + Shift + I`) and install:
   - `LiquidCrystal_I2C` by Frank de Brabander
   - `DHT sensor library` by Adafruit (and agree to install `Adafruit Unified Sensor`)
   - If using ESP32: `ESP32Servo` by Kevin Harrington
   - If using ESP8266: built-in `Servo` library is used automatically

3. **Configure Wi-Fi & PC IP**:
   Find your computer's local IP on your Wi-Fi network:
   - **Windows**: Open cmd/powershell, run `ipconfig`, look for `IPv4 Address` (e.g., `192.168.1.50` or `10.x.x.x`).
   - **Mac/Linux**: Run `hostname -I` or `ip a`.

   In `firmware/smart_dustbin/smart_dustbin.ino`, update lines 52–57:
   ```cpp
   // 1. Enter your Wi-Fi credentials (must be 2.4 GHz network)
   const char* WIFI_SSID     = "YOUR_WIFI_NAME";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

   // 2. Local IP address of the PC running the Node.js backend
   const char* SERVER_URL    = "http://YOUR_COMPUTER_IP:3000/api/readings";

   // 3. Bin identifier matching registered bin
   const char* BIN_ID        = "bin-01";
   ```

4. **Calibrate Dustbin Height**:
   Measure your physical dustbin and adjust:
   ```cpp
   // Distance from ultrasonic sensor face to bottom of empty bin (cm)
   const float BIN_EMPTY_DISTANCE_CM = 15.0;

   // Distance from ultrasonic sensor face when bin is 100% full (cm)
   const float BIN_FULL_DISTANCE_CM  = 3.0;
   ```

5. **Upload**:
   - Select your board under **Tools -> Board** (`ESP32 Dev Module` or `NodeMCU 1.0`).
   - Select the correct COM port under **Tools -> Port**.
   - Click **Upload**.
   - Open **Serial Monitor** at **9600 baud** to verify Wi-Fi connection and sensor telemetry.

---

### 5. Switching Dashboard to Physical Hardware Mode

By default, the dashboard runs 6 simulated campus bins. When your physical hardware is ready:

```bash
# Run this from the repository root:
npm run setup-hardware
```

This helper script:
- Configures `bin-01` as the active **Physical Smart Bin** matching your sensor calibration.
- Pauses the background simulation ticks so simulated data never overwrites your live hardware telemetry.
- Removes demo bins so your physical dustbin is front and center.

---

## 🛠️ Troubleshooting

| Issue | Cause & Solution |
| :--- | :--- |
| **`Cannot find module 'node:sqlite'`** | Node.js is older than version 24. Run `node -v` and update Node to v24+ from [nodejs.org](https://nodejs.org). |
| **Wi-Fi connection fails on ESP** | ESP32/ESP8266 only supports **2.4 GHz Wi-Fi networks**. Make sure you are not connecting to a 5 GHz-only network. |
| **HTTP POST error / Connection refused** | 1. Ensure your PC and ESP are on the same Wi-Fi network.<br>2. Check Windows Firewall: allow incoming connections on port 3000 or temporarily test with firewall off.<br>3. Verify your PC IP address did not change with `ipconfig`. |
| **LCD displays blue squares / nothing** | 1. Adjust the small blue contrast potentiometer on the back of the I2C backpack using a screwdriver.<br>2. If text still does not appear, your I2C address might be `0x3F` instead of `0x27`. Run an Arduino I2C scanner sketch to verify. |
| **ESP board resets when lid opens** | The servo motor is drawing too much surge current from the ESP 3.3V/5V pin. Power the servo from an external 5V power supply (share GND with ESP). |
| **False ultrasonic readings** | The firmware automatically pauses ultrasonic readings while the lid is open or moving to prevent false echoes off the lid. Make sure the sensor has a clear downward view. |

---

## 📁 Repository Structure

```text
smart-dustbin/
├── package.json               # Root scripts (start, test, setup-hardware)
├── .gitignore                 # Clean repository exclusions
├── README.md                  # Master setup guide (this file)
│
├── dashboard/                 # Full-stack Collector Dashboard
│   ├── server.js              # Express REST API & simulation engine
│   ├── store.js               # SQLite data layer & calibration algorithms
│   ├── setup-hardware-bin.js  # Switch dashboard to live physical bin
│   ├── launch.js              # Idempotent browser launcher
│   ├── Start Dashboard.cmd    # 1-click Windows launcher
│   ├── public/                # Vanilla JS / CSS frontend (no bundler required)
│   └── test/                  # Store test suite (node --test)
│
├── firmware/
│   └── smart_dustbin/
│       └── smart_dustbin.ino  # ESP32 / ESP8266 edge firmware (C++)
│
├── md/                        # Comprehensive course documentation & specs
│   ├── ARCHITECTURE.md        # Deep dive into dual-loop system architecture
│   ├── HARDWARE_AND_PINOUT.md # Circuit schematics & electronic specifications
│   ├── BACKEND_AND_DATABASE.md# Algorithmic specs & SQLite schema
│   ├── API_REFERENCE.md       # Complete REST API specifications
│   └── DEVELOPER_GUIDE.md     # Developer notes & maintenance
│
└── output/                    # Deliverables & Course Specs
    ├── latex/                 # Academic LaTeX report
    └── pdf/                   # Compiled SRS PDF
```

---

## 📄 License & Credits
Developed for academic research and IoT smart campus demonstrations at Bangladesh University of Professionals (BUP).
