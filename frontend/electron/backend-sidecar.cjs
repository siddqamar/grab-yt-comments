const { app } = require('electron');
const { execFileSync, spawn } = require('node:child_process');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

const DEFAULT_BACKEND_HOST = '127.0.0.1';
const DEFAULT_BACKEND_PORT = '8000';
const PACKAGED_BACKEND_NAME = 'grab-yt-comments-api.exe';
const HEALTH_TIMEOUT_MS = 15000;
const HEALTH_INTERVAL_MS = 500;
const WINDOWS_STOP_TIMEOUT_MS = 5000;
const WINDOWS_STOP_RETRY_MS = 250;
const stopSleepSignal = new Int32Array(new SharedArrayBuffer(4));

function windowsSystemExecutable(name) {
  const systemRoot = process.env.SystemRoot || 'C:\\Windows';
  return path.join(systemRoot, 'System32', `${name}.exe`);
}

function windowsPowerShellExecutable() {
  const systemRoot = process.env.SystemRoot || 'C:\\Windows';
  return path.join(systemRoot, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
}

function sleepMs(timeoutMs) {
  Atomics.wait(stopSleepSignal, 0, 0, timeoutMs);
}

function backendRuntimeEnv() {
  const env = { ...process.env };
  if (!env.CLASSIFICATION_DB_PATH && app) {
    env.CLASSIFICATION_DB_PATH = path.join(app.getPath('userData'), 'classification-cache.sqlite3');
  }
  return env;
}

function packagedBackendExecutable() {
  return path.join(process.resourcesPath, 'backend', PACKAGED_BACKEND_NAME);
}

function backendConfig() {
  const host = process.env.DESKTOP_BACKEND_HOST || DEFAULT_BACKEND_HOST;
  const port = process.env.DESKTOP_BACKEND_PORT || DEFAULT_BACKEND_PORT;
  const repoRoot = path.resolve(__dirname, '..', '..');
  const backendCwd = process.env.DESKTOP_BACKEND_CWD || path.join(repoRoot, 'backend');
  const venvPython = path.join(backendCwd, '.venv', 'Scripts', 'python.exe');
  const packagedExecutable = packagedBackendExecutable();
  const explicitCommand = process.env.DESKTOP_BACKEND_COMMAND;

  if (!explicitCommand && app.isPackaged) {
    if (!fs.existsSync(packagedExecutable)) {
      throw new Error(`Packaged backend executable not found at ${packagedExecutable}`);
    }

    return {
      host,
      port,
      url: `http://${host}:${port}`,
      cwd: path.dirname(packagedExecutable),
      command: packagedExecutable,
      args: ['--host', host, '--port', port],
      env: backendRuntimeEnv(),
    };
  }

  return {
    host,
    port,
    url: `http://${host}:${port}`,
    cwd: backendCwd,
    command: explicitCommand || (fs.existsSync(venvPython) ? venvPython : 'python'),
    args: [
      '-m',
      'uvicorn',
      'api:app',
      '--host',
      host,
      '--port',
      port,
    ],
    env: backendRuntimeEnv(),
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
    const output = execFileSync(windowsSystemExecutable('netstat'), ['-ano'], { encoding: 'utf8' });
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
    execFileSync(
      windowsPowerShellExecutable(),
      ['-NoProfile', '-NonInteractive', '-Command', `Stop-Process -Id ${pid} -Force`],
      { stdio: 'ignore' }
    );
  } catch {
    // The process may have already exited between detection and shutdown.
  }
}

function stopWindowsListeners(port) {
  const deadline = Date.now() + WINDOWS_STOP_TIMEOUT_MS;

  while (Date.now() < deadline) {
    const pids = listeningPids(port);
    if (pids.length === 0) {
      return;
    }

    for (const pid of pids) {
      killWindowsProcessTree(pid);
    }

    sleepMs(WINDOWS_STOP_RETRY_MS);
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
    env: config.env,
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

        stopWindowsListeners(config.port);
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
  packagedBackendExecutable,
  startBackendSidecar,
  waitForHealth,
};
