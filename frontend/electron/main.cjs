const { app, BrowserWindow } = require('electron');
const { startBackendSidecar } = require('./backend-sidecar.cjs');

const DEFAULT_RENDERER_URL = 'http://localhost:3000';
const autoQuitAfterMs = Number(process.env.DESKTOP_AUTO_QUIT_AFTER_MS || 0);
let backendSidecar;

function createMainWindow() {
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
      sandbox: true,
    },
  });

  mainWindow.on('close', stopBackendSidecar);
  mainWindow.on('closed', stopBackendSidecar);

  const rendererUrl = process.env.DESKTOP_RENDERER_URL || DEFAULT_RENDERER_URL;
  void mainWindow.loadURL(rendererUrl);
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

  createMainWindow();
  if (Number.isFinite(autoQuitAfterMs) && autoQuitAfterMs > 0) {
    setTimeout(() => {
      stopBackendSidecar();
      app.exit(0);
    }, autoQuitAfterMs);
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
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
