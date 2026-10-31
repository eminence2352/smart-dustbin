# Smart Dustbin collector dashboard

Local demo using Express, SQLite and plain JavaScript. Every bin is simulated. Fonts are served locally and no internet is needed after installation.

## Run

From `F:\smart dustbin`, run `npm.cmd start`. The workspace shortcut starts the dashboard or tells you if it is already running.

Requires Node.js 24 or newer.

```sh
npm install
npm start
```

Open http://localhost:3000. Other devices on the same WiFi can use the computer's local IP and port 3000, if allowed by its firewall. This is a trusted local demo, with no login.

## Demonstrate

1. View the six simulated campus bins. Sample history is created once in SQLite.
2. Choose **Send a reading**, then choose a bin and enter raw distance, temperature, humidity and new lid openings. Presets only populate distance; submit to save.
3. Sending a reading pauses that bin's automatic updates. The three-reading option demonstrates stability and counts openings once. Send 75% then 6% to see automatic collection detection.
4. Blank sensor fields send null. A failed distance reading retains explicitly labelled last known fill; other valid fields still update.
5. Use **Mark as collected** to manually record an emptying. It resets counts, not fill.
6. **Pause demo** stops all generated readings. Bins become offline after 30 seconds. Resume a manually held bin on its detail page. One example bin begins paused to demonstrate offline status.

Fill calibration is 40 cm empty and 5 cm full. Stable fill needs three valid values within five points. Collection detection compares stable fill from at least 70% to at most 10%. Prediction uses at least five stable points spanning ten minutes and a positive fill trend; all predictions are labelled estimates. Display time is Asia/Dhaka.

## API

`POST /api/readings` accepts `{binId, distanceCm, tempC, humidity, opensDelta, requestId?}`. Numeric sensor fields are nullable. Reuse the optional requestId for safe retries. Device and demo data go through this same validation and calculation path.

`GET /api/bins`, `GET /api/bins/:id`, reading and collection history endpoints are available. `POST /api/bins/:id/collect` requires a unique requestId. SQLite lives in smartbin.db and survives restarts.

Run `npm test` for calculation, collection detection, retry and persistence checks. Source layout: server.js for HTTP and simulation, store.js for data and rules, public/ for the interface. Built-in Node SQLite avoids native addon setup on Windows.
