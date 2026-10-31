# System Requirements Specification (SRS)

This document provides a consolidated reference for the formal requirements of the **Smart Dustbin** project, developed for the Computer Interfacing Laboratory (Course Code: **CSE 4102**, Group 06, Bangladesh University of Professionals).

---

## 1. Project Metadata & Academic Scope

- **Institution**: Bangladesh University of Professionals (BUP)
- **Faculty**: Faculty of Science and Technology, Dept. of Computer Science and Engineering
- **Course**: Computer Interfacing Laboratory (CSE 4102, Section B)
- **Group 06 Members**:
  - Sheikh Sifat Rahman (ID: 23524242108)
  - Sajid Al Adeeb (ID: 23524242030)
  - Abdullah Towhid (ID: 23524242054)
  - Taqi Tahmid (ID: 23524242110)
- **Primary Deliverables**: 
  - One physical prototype bin with an ESP32 node.
  - Five simulated bins for realistic campus-scale multi-unit testing.
  - A local backend server, SQLite database, and web collector dashboard.

---

## 2. User Requirements (UR)

| ID | User Requirement Description |
| :--- | :--- |
| **UR01** | The system shall open the lid when a hand is detected near the IR obstacle sensor. |
| **UR02** | The system shall close the lid after the hand has been removed for the configured time. |
| **UR03** | The system shall let a collector view all registered bins and open a separate page for each bin. |
| **UR04** | The system shall show a bin's address, fill level, last collection time, and number of lid openings since collection. |
| **UR05** | The system shall show temperature, humidity, connection status, and the time of the latest reading. |
| **UR06** | The system shall show an estimated next collection time, or explain why there is not enough data to calculate it. |
| **UR07** | The system shall let the collector mark a bin as collected after emptying it. |
| **UR08** | The system shall continue local lid operation when Wi-Fi is unavailable and distinguish physical bins from simulated bins. |

---

## 3. Functional Requirements (FR)

### At the Physical Bin Edge
- **FR01 (IR Hand Detection & Actuation)**: The ESP32 shall use the IR sensor for hand detection and the SG90 servo for lid movement. A hand that remains in front of the sensor shall not trigger repeated open/close cycles.
- **FR02 (Lid Stay-Open and Clear Delay)**: The lid shall remain open while a hand is detected. After the area stays clear for 3 seconds, the lid shall close. A 2-second cooldown shall prevent immediate re-triggering. Detection during closing shall request reopening.
- **FR03 (Usage Counter)**: The controller shall add one usage event when an opening movement completes. The count represents commanded opening cycles (not trash item count).
- **FR04 (Ultrasonic Fill Measurement)**: One ultrasonic sensor shall measure distance to waste. It shall **not** take fill samples while the lid is open or during the 2-second settling period after closing. The device shall send the median of five usable samples, or null when unavailable.
- **FR05 (Climate Readings)**: The DHT11 shall provide temperature and humidity. A failed reading shall be sent as `null` rather than zero.
- **FR06 (Telemetry Frequency)**: The ESP32 shall send readings and opening increments every 5 to 10 seconds. Pending opening counts shall remain available for retry when a request fails.
- **FR07 (Local LCD Feedback)**: The 16x2 I2C LCD shall display temperature, humidity, Wi-Fi state, and the latest fill percentage returned by the backend.
- **FR08 (Fail-Safe Local Operation)**: The controller shall continue checking the hand sensor during network failures. On reboot, it shall initialize without recording false opening events.

### At the Backend Server & Dashboard
- **FR09 (Payload Ingestion & Deduplication)**: The backend shall accept readings for registered bin IDs, validate numeric ranges, and save them with server timestamps. Repeated submissions using the same `requestId` shall not add the opening count twice.
- **FR10 (Fill Calculation and Partial Fault Tolerance)**: The backend shall calculate fill percentage from calibrated empty ($E$) and full ($F$) distances. If distance is invalid, it shall be excluded from fill updates while still recording valid openings, temperature, and humidity.
- **FR11 (Automatic Collection Detection)**: The backend shall compare stable fill values (median of 3 readings within 5% spread). A transition from $\ge 70\%$ down to $\le 10\%$ shall record an automatic collection and reset the usage counter.
- **FR12 (Manual Collection Action)**: Manual collection shall prompt for confirmation, save a collection record with method `'manual'`, reset usage count to 0, and clear earlier stability windows without manufacturing an artificial 0% fill reading.
- **FR13 (Collection ETA Projection)**: The backend shall estimate time to the 90% target only when at least 5 stable readings spanning at least 10 minutes exist with a positive fill rate.
- **FR14 (Dashboard Views & History)**: The dashboard shall display a bin overview list, single bin detail views with SVG trend charts, and complete collection histories.
- **FR15 (Heartbeat & Offline Status)**: A bin without an accepted reading for $>30$ seconds shall be marked as `Offline`. Times shall be rendered in `Asia/Dhaka`.
- **FR16 (Simulation Transparency)**: Simulated bins shall use the exact same ingestion API as physical hardware and shall be explicitly labelled on the dashboard.
- **FR17 (Persistence)**: All bin records, telemetry history, and collection events shall persist across server restarts in SQLite.

---

## 4. Non-Functional Requirements (NFR)

| ID | Quality | Specification Target | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR01** | Accuracy | 9 of 10 settled readings at 5 test heights within $\pm 5\%$ of calibrated fill. | Lab test bench measurement. |
| **NFR02** | Response | Lid begins opening within $\le 1\text{ s}$ of hand detection. Ingested reading appears on UI within $\le 15\text{ s}$. | Video frame timing / network trace. |
| **NFR03** | Reliability | 30-minute test run without crash/reset. 60-second Wi-Fi outage does not interrupt lid mechanism. | Extended soak test. |
| **NFR04** | Mechanical Safety | Servo travel limits enforced. Continuous hand presence holds lid open. | Physical obstruction testing. |
| **NFR05** | Electrical Safety | HC-SR04 ECHO passed through voltage divider ($\le 3.3\text{ V}$). Servo powered from 5V rail with common ground. | Multimeter / oscilloscope verification. |
| **NFR06** | Power Integrity | Power supply handles peak Wi-Fi and servo stall current. 20 consecutive lid cycles cause no brownout. | Rapid trigger stress test. |
| **NFR07** | Usability | Bin detail reachable in 1 click. Missing data displayed as `—` (never misleading 0). | UI walkthrough. |
| **NFR08** | Local Offline Operation | Complete dashboard and fonts load with zero external internet access. | Disconnect WAN, test on local hotspot. |
| **NFR09** | Maintainability | Calibration values isolated in configuration. Clean separation of UI, server, and store. | Code architecture review. |
| **NFR10** | Input Validation | All HTTP inputs validated against range constraints. | API fuzzing / unit tests. |

---

## 5. Acceptance Test Plan (T01 – T12)

The system includes a 12-stage acceptance testing suite defined in the SRS:

| Test ID | Covered Req | Action | Expected Result |
| :---: | :--- | :--- | :--- |
| **T01** | FR01–FR03 | Hold hand in front of IR sensor for 10s, then release. | 1 opening counted. Lid stays open 10s, closes 3s after release. |
| **T02** | FR04, FR10, NFR01 | Test 10 ultrasonic samples at 5 known container heights. | $\ge 90\%$ of readings within $\pm 5\%$ calibrated fill. |
| **T03** | FR05, FR09, FR10 | Post null distance with `opensDelta: 2`. | Openings increment by 2; fill retains last valid reading. |
| **T04** | FR11 | Post 3 readings at 75%, followed by 3 readings at 8%. | Exactly 1 automatic collection event recorded. Usage reset. |
| **T05** | FR11 | Post a single 5% reading in between 75% readings. | No collection recorded (rejected as single transient outlier). |
| **T06** | FR06, FR09, FR17 | Send identical payload twice with the same `requestId`. | Acknowledged on second attempt without double-counting openings. |
| **T07** | FR08, FR15 | Cut Wi-Fi for 60s while waving hand at IR sensor. | Lid continues to cycle. UI marks bin offline after 30s. |
| **T08** | FR12 | Confirm manual collection, retry submission, then post fresh low reading. | Exactly 1 manual event recorded. Usage reset once. |
| **T09** | FR13 | Test flat trend, rising trend, and $\ge 90\%$ fill. | Displays reason when data insufficient; displays valid ETA on rising trend; "Collect now" at 90%. |
| **T10** | FR09, FR16, FR17 | Submit invalid payload (e.g. humidity 101); restart server. | Invalid payload rejected (HTTP 400). Data preserved after restart. |
| **T11** | NFR02–NFR06 | Run 20 rapid lid cycles while measuring supply voltage. | No ESP32 brownout reboot. Timing targets met. |
| **T12** | FR07, FR14, NFR07, NFR08 | Disconnect WAN internet connection; browse all pages. | All pages, local fonts, and SVG charts function fully offline. |
