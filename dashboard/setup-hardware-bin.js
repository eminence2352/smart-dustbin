import { createStore } from './store.js';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const store = createStore(path.join(root, 'smartbin.db'));

const binId = process.argv[2] || 'bin-01';
const emptyDistance = parseFloat(process.argv[3]) || 15.0;
const fullDistance = parseFloat(process.argv[4]) || 3.0;

// Ensure seed has run if db was empty
store.seed();

const bin = store.get(binId);
if (!bin) {
  console.error(`Error: Bin '${binId}' not found in database.`);
  process.exit(1);
}

bin.name = 'Physical Smart Bin';
bin.emptyDistance = emptyDistance;
bin.fullDistance = fullDistance;
bin.paused = true; // Prevents simulated ticks from overwriting live hardware telemetry

store.save(bin);

// Remove all other bins and their simulated history so ONLY this 1 dustbin stays active
store.db.exec("DELETE FROM bins WHERE id != '" + binId + "'");
store.db.exec("DELETE FROM readings WHERE bin_id != '" + binId + "'");
store.db.exec("DELETE FROM collections WHERE bin_id != '" + binId + "'");

console.log(`\n[SUCCESS] Only 1 dustbin is now active on the dashboard: '${binId}'`);
console.log(`- Name: ${bin.name}`);
console.log(`- Empty Distance (bottom of bin): ${bin.emptyDistance} cm`);
console.log(`- Full Distance (top rim): ${bin.fullDistance} cm`);
console.log(`- Simulation: PAUSED (reserved for live hardware readings)`);
console.log(`- Other bins: REMOVED (dashboard only displays this single active dustbin)\n`);
