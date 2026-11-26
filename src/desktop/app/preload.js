const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('baNative', {
  loadSave: () => ipcRenderer.sendSync('save-load'),
  writeSave: o => ipcRenderer.send('save-write', o),
  quit: () => ipcRenderer.send('quit'),
  setFullscreen: on => ipcRenderer.send('fs-set', !!on),
  isFullscreen: () => ipcRenderer.sendSync('fs-get'),
  achieve: id => ipcRenderer.send('ach', String(id)),
  dev: ipcRenderer.sendSync('dev'),
  mp: {   // multiplayer over Steam (see main.js)
    ok: () => ipcRenderer.sendSync('mp-ok'),
    host: max => ipcRenderer.invoke('mp-host', max),
    join: code => ipcRenderer.invoke('mp-join', String(code)),
    info: () => ipcRenderer.invoke('mp-info'),
    leave: () => ipcRenderer.send('mp-leave'),
    setData: (k, v) => ipcRenderer.send('mp-data', String(k), String(v)),
    send: (to, data, reliable) => ipcRenderer.send('mp-send', String(to), String(data), !!reliable),
    onMsg: cb => ipcRenderer.on('mp-msg', (e, from, data) => cb(from, data)),
    onLobby: cb => ipcRenderer.on('mp-lobby', (e, info) => cb(info)),
  },
});
