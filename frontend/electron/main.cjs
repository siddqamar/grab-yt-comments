const { app, BrowserWindow } = require('electron');
const path = require('node:path');
const { startBackendSidecar } = require('./backend-sidecar.cjs');

const DEFAULT_RENDERER_URL = 'http://localhost:3000';
const autoQuitAfterMs = Number(process.env.DESKTOP_AUTO_QUIT_AFTER_MS || 0);
let backendSidecar;

function rendererEntry() {
  if (process.env.DESKTOP_RENDERER_URL) {
    return { kind: 'url', value: process.env.DESKTOP_RENDERER_URL };
  }

  if (app.isPackaged) {
    return {
      kind: 'file',
      value: path.join(__dirname, '..', 'dist', 'index.html'),
    };
  }

  return { kind: 'url', value: DEFAULT_RENDERER_URL };
}

function createMainWindow(apiBaseUrl) {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: '#050505',
    title: 'GrabComments',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.cjs'),
      additionalArguments: [`--api-base-url=${apiBaseUrl}`],
      sandbox: true,
    },
  });

  mainWindow.on('close', stopBackendSidecar);
  mainWindow.on('closed', stopBackendSidecar);

  const entry = rendererEntry();
  if (entry.kind === 'file') {
    void mainWindow.loadFile(entry.value);
    return;
  }

  void mainWindow.loadURL(entry.value);
}

function stopBackendSidecar() {
  if (backendSidecar) {
    backendSidecar.stop();
    backendSidecar = undefined;
  }
}

app.whenReady().then(async () => {
  try {
    backendSidecar = startBackendSidecar();
    const backendReady = await backendSidecar.waitUntilReady();
    if (!backendReady) {
      console.error(`Backend sidecar did not become healthy at ${backendSidecar.url}/health`);
    }
  } catch (error) {
    console.error(error.message);
    app.quit();
    return;
  }

  createMainWindow(backendSidecar.url);
  if (Number.isFinite(autoQuitAfterMs) && autoQuitAfterMs > 0) {
    setTimeout(() => {
      stopBackendSidecar();
      app.exit(0);
    }, autoQuitAfterMs);
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow(backendSidecar?.url);
    }
  });
});

app.on('window-all-closed', () => {
  stopBackendSidecar();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', stopBackendSidecar);
app.on('quit', stopBackendSidecar);
