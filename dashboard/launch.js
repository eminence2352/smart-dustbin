import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const port = Number(process.env.PORT) || 3000;
const url = `http://localhost:${port}`;
let alreadyRunning = false;
try {
  const response = await fetch(`${url}/api/bins`, {
    signal: AbortSignal.timeout(1500),
  });
  const data = await response.json();
  alreadyRunning = response.ok && typeof data.running === 'boolean'
    && Array.isArray(data.bins) && data.bins.length > 0
    && data.bins.every(bin => bin.source === 'simulated' && /^bin-\d+$/.test(bin.id));
} catch {
  // No existing dashboard responded. Start the application below.
}

if (alreadyRunning) {
  console.log(`Smart Dustbin is already running. Open ${url}`);
} else {
  const child = spawn(process.execPath, [fileURLToPath(new URL('./server.js', import.meta.url))], {
    stdio: 'inherit',
  });
  child.on('error', error => {
    console.error(`Could not start the dashboard: ${error.message}`);
    process.exitCode = 1;
  });
  child.on('exit', code => { process.exitCode = code ?? 0; });
}
