# Frontend Dashboard Architecture

This document details the user interface architecture, client-side routing, styling system, and custom SVG charting implemented in [`dashboard/public/`](file:///f:/smart%20dustbin/dashboard/public/).

---

## 1. Design Philosophy & Technology Stack

The collector dashboard is engineered as an ultra-reliable, zero-dependency, local-first web application:
- **No Build Tools**: Runs directly from standard browser ES6 modules without Webpack, Vite, Babel, or bundling steps.
- **Offline Self-Sufficiency**: Locally packages variable font files (`Manrope` for UI text and `Space Grotesk` for numbers/headings) so no internet connection or Google Fonts CDN is needed.
- **Native Web Standards**: Built using vanilla DOM APIs, native HTML5 `<dialog>` elements for modals, and inline SVG rendering.

---

## 2. Directory Structure

```text
dashboard/public/
├── index.html       # Single-page application skeleton, navigation sidebar, dialog markup
├── app.js           # Single-file ES6 application, router, state, SVG rendering, forms
├── style.css        # Scoped design system, CSS variables, dark/light balanced theme
└── fonts/           # Local font directories mapped via Express static routes
```

---

## 3. Client-Side Hash Routing

Navigation is controlled entirely through `window.location.hash`, managed in `app.js`:

```mermaid
flowchart TD
    HASH[window.location.hash] --> PARSE{Route Match}
    PARSE -- "#overview" or empty --> R_OVERVIEW[renderOverview()]
    PARSE -- "#bin/:id" --> R_DETAIL[renderBinDetail(id)]
    PARSE -- "#collections" --> R_LOG[renderCollectionsLog()]

    R_OVERVIEW --> VIEW[Inject into #main element]
    R_DETAIL --> VIEW
    R_LOG --> VIEW
```

### Route Handlers:
1. **`#overview`**: Displays high-level campus metrics (Total Bins, Attention Needed, Average Fill, Active Online Bins), filter toggles, instant search box, and a grid of interactive bin cards.
2. **`#bin/:id`**: Deep-dive page displaying real-time sensor measurements, historical SVG fill charts, ETA predictions, manual collection actions, and specific collection logs.
3. **`#collections`**: Consolidated log table of all historical collection events across every bin on campus.

---

## 4. Visual State & Threshold Badging

Every bin's operational status is calculated in `status(bin)`:

| Fill Range | Online? | Valid? | Badge Label | Color Class |
| :--- | :---: | :---: | :--- | :--- |
| Any | **False** | — | `Offline` | `gray` |
| Any | True | **False** | `Sensor unavailable` | `gray` |
| $\ge 90\%$ | True | True | `Needs collection` | `red` |
| $80\% - 89.9\%$ | True | True | `Nearly full` | `red` |
| $50\% - 79.9\%$ | True | True | `Filling up` | `yellow` |
| $0\% - 49.9\%$ | True | True | `Normal` | `green` |

---

## 5. Native SVG Charting Engine

Rather than loading large charting libraries (Chart.js or D3), `app.js` generates pure SVG path strings directly from reading arrays in `chart(readings)`:

- **Dimensions**: ViewBox `0 0 590 207`.
- **Target Line**: Dotted horizontal rule plotted at the $90\%$ target level (`stroke="#d1b593"`).
- **Trend Curve**: Generates continuous SVG path strings (`M x,y L x,y`) mapping timestamps to the X-axis and fill percentages ($0–100\%$) to the Y-axis.
- **Handling Nulls**: When distance readings fail or the lid is open, the path generator lifts the pen (`pen = false`) and only resumes when a valid reading occurs, preventing erroneous drops to $0\%$.

```text
100% ┌────────────────────────────────────────────────────────┐
     │                                                        │
 90% ├ - - - - - - - - - - - - - - - - - - - - - - - - - - - -┤ (Collection Target)
     │                                       ╭────────*       │
 50% ├───────────────────────╭───────────────╯                │
     │                      ╭╯                                │
  0% └──────────────────────┴─────────────────────────────────┘
    Start Time                                         Latest Reading
```

---

## 6. Interactive Dialogs & Modals

### 6.1 Demo Controls Dialog (`#controls`)
Allows manual injection of sensor data for testing and presentations:
- **Preset Buttons**: Quick-fills distance for common scenarios:
  - *Low* ($25\% \rightarrow 31.25\text{ cm}$)
  - *Filling up* ($75\% \rightarrow 13.75\text{ cm}$)
  - *Nearly full* ($94\% \rightarrow 7.10\text{ cm}$)
  - *Emptied* ($6\% \rightarrow 37.90\text{ cm}$)
- **Batching Option**: "Send 3 readings to settle the measurement" checkbox automatically issues 3 sequential readings to immediately satisfy the 3-point stability window algorithm.
- **Automatic Simulation Pausing**: When a manual reading is sent for a bin, background simulation is paused for that bin so user inputs remain visible.

### 6.2 Manual Collection Confirmation (`#confirm`)
- Prompts user confirmation before marking a bin as collected.
- Generates a unique UUID `requestId` upon modal open.
- Disables the confirmation button during submission to prevent duplicate clicks.

---

## 7. Polling & Input Preservation

The dashboard continuously synchronizes with the server every **5000 ms**:
- If the user is currently typing in the search box, `refresh()` captures `selectionStart` and restores cursor position and focus immediately after DOM updates.
- If network errors occur, an accessible error banner (`role="alert"`) appears without crashing the page.
- Header clock displays local time formatted in the `Asia/Dhaka` time zone.
