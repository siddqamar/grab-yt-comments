const { contextBridge } = require('electron');

function apiBaseUrlFromArgs() {
  const prefix = '--api-base-url=';
  const argument = process.argv.find((value) => value.startsWith(prefix));
  return argument ? argument.slice(prefix.length) : undefined;
}

contextBridge.exposeInMainWorld('desktopConfig', {
  apiBaseUrl: apiBaseUrlFromArgs(),
});
