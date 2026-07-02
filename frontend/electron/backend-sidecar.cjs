const { execFileSync, spawn } = require('node:child_process');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

const DEFAULT_BACKEND_HOST = '127.0.0.1';
const DEFAULT_BACKEND_PORT = '8000';
const HEALTH_TIMEOUT_MS = 15000;
const HEALTH_INTERVAL_MS = 500;

function backendConfig() {
  const host = process.env.DESKTOP_BACKEND_HOST || DEFAULT_BACKEND_HOST;
  const port = process.env.DESKTOP_BACKEND_PORT || DEFAULT_BACKEND_PORT;
  const repoRoot = path.resolve(__dirname, '..', '..');
  const backendCwd = process.env.DESKTOP_BACKEND_CWD || path.join(repoRoot, 'backend');
  const venvPython = path.join(backendCwd, '.venv', 'Scripts', 'python.exe');

  return {
    host,
    port,
    url: `http://${host}:${port}`,
    cwd: backendCwd,
    command: process.env.DESKTOP_BACKEND_COMMAND || (fs.existsSync(venvPython) ? venvPython : 'python'),
    args: [
      '-m',
      'uvicorn',
      'api:app',
      '--host',
      host,
      '--port',
      port,
    ],
  };
}

function requestHealth(healthUrl) {
  return new Promise((resolve) => {
    const request = http.get(healthUrl, (response) => {
      response.resume();
      resolve(response.statusCode === 200);
    });

    request.on('error', () => resolve(false));
    request.setTimeout(1000, () => {
      request.destroy();
      resolve(false);
    });
  });
}

async function waitForHealth(baseUrl, timeoutMs = HEALTH_TIMEOUT_MS) {
  const healthUrl = `${baseUrl}/health`;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    if (await requestHealth(healthUrl)) {
      return true;
    }

    await new Promise((resolve) => setTimeout(resolve, HEALTH_INTERVAL_MS));
  }

  return false;
}

function listeningPids(port) {
  if (process.platform !== 'win32') {
    return [];
  }

  try {
    const output = execFileSync('netstat', ['-ano'], { encoding: 'utf8' });
    return output
      .split(/\r?\n/)
      .map((line) => line.trim().split(/\s+/))
      .filter((parts) => parts[0] === 'TCP' && parts[1]?.endsWith(`:${port}`) && parts[3] === 'LISTENING')
      .map((parts) => Number(parts[4]))
      .filter((pid) => Number.isInteger(pid) && pid > 0);
  } catch {
    return [];
  }
}

function killWindowsProcessTree(pid) {
  try {
    execFileSync('taskkill', ['/pid', String(pid), '/t', '/f'], { stdio: 'ignore' });
  } catch {
    // The process may have already exited between detection and shutdown.
  }
}

function startBackendSidecar() {
  const config = backendConfig();
  const existingListenerPids = listeningPids(config.port);
  if (existingListenerPids.length > 0) {
    throw new Error(`Backend sidecar port ${config.port} is already in use`);
  }

  const child = spawn(config.command, config.args, {
    cwd: config.cwd,
    env: process.env,
    stdio: 'ignore',
    windowsHide: true,
  });

  child.on('error', (error) => {
    console.error(`Backend sidecar failed to start: ${error.message}`);
  });

  return {
    child,
    url: config.url,
    async waitUntilReady() {
      return waitForHealth(config.url);
    },
    stop() {
      if (process.platform === 'win32') {
        if (child.pid) {
          killWindowsProcessTree(child.pid);
        }

        for (const pid of listeningPids(config.port)) {
          killWindowsProcessTree(pid);
        }
      } else {
        if (!child.killed && child.exitCode === null) {
          child.kill();
        }
      }
    },
  };
}

module.exports = {
  backendConfig,
  startBackendSidecar,
  waitForHealth,
};
