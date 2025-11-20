const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  scanWiFi: () => ipcRenderer.invoke('scan-wifi')
});
