const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('baNative', {
  loadSave: () => ipcRenderer.sendSync('save-load'),
  writeSave: o => ipcRenderer.send('save-write', o),
  quit: () => ipcRenderer.send('quit'),
  setFullscreen: on => ipcRenderer.send('fs-set', !!on),
  isFullscreen: () => ipcRenderer.sendSync('fs-get'),
  achieve: id => ipcRenderer.send('ach', String(id)),
  dev: ipcRenderer.sendSync('dev'),
});
