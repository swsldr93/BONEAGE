// Bone Age: desktop wrapper for Steam (Electron).
const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const fs = require('fs');

// Steam sets SteamAppId when it launches the game. FALLBACK_APP_ID is only used when you run the exe directly while testing.
const FALLBACK_APP_ID = 5633130; // Bone Age on Steam (outside Steam the signed-in account must own it, or have a key)
let steam = null;
try {
  const id = Number(process.env.SteamAppId) || FALLBACK_APP_ID;
  if (id) steam = require('steamworks.js').init(id);
} catch (e) { steam = null; console.warn('Steam not available:', e && e.message); }

app.setName('Bone Age');
const saveDir = app.getPath('userData');
const saveFile = path.join(saveDir, 'save.json'); // Steam Auto-Cloud: sync this one file
function loadSave() { try { const o = JSON.parse(fs.readFileSync(saveFile, 'utf8')); return (o && typeof o === 'object') ? o : {}; } catch (e) { return {}; } }
function writeSave(o) { try { fs.mkdirSync(saveDir, { recursive: true }); const tmp = saveFile + '.tmp'; fs.writeFileSync(tmp, JSON.stringify(o)); fs.renameSync(tmp, saveFile); } catch (e) { console.error('save failed', e); } }

let win = null;
function create() {
  const st = loadSave().settings || {};
  win = new BrowserWindow({
    width: 1600, height: 900, minWidth: 960, minHeight: 600,
    backgroundColor: '#000000', show: false, title: 'Bone Age', icon: path.join(__dirname, 'icon.png'),
    fullscreen: st.full !== 0, autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false, sandbox: true,
      backgroundThrottling: false, autoplayPolicy: 'no-user-gesture-required', spellcheck: false,
    },
  });
  win.loadFile(path.join(__dirname, 'index.html'));
  win.once('ready-to-show', () => win.show());
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (e, url) => { if (!url.startsWith('file:')) e.preventDefault(); });
}

if (process.platform === 'darwin') Menu.setApplicationMenu(Menu.buildFromTemplate([{ role: 'appMenu' }, { role: 'windowMenu' }]));
else Menu.setApplicationMenu(null);

ipcMain.on('save-load', e => { e.returnValue = loadSave(); });
ipcMain.on('save-write', (e, o) => writeSave(o));
ipcMain.on('quit', () => app.quit());
ipcMain.on('fs-set', (e, on) => { if (win) win.setFullScreen(!!on); });
ipcMain.on('fs-get', e => { e.returnValue = !!(win && win.isFullScreen()); });
ipcMain.on('dev', e => { e.returnValue = process.argv.includes('--dev'); });
ipcMain.on('ach', (e, id) => { try { if (steam && !steam.achievement.isActivated(id)) steam.achievement.activate(id); } catch (err) { console.warn('achievement', id, err && err.message); } });

/* ---------- multiplayer over Steam: a lobby holds the players; messages go player to player through Steam's relays.
   The room code is the lobby's own id, the low 32 bits written in 7 letters (the high bits are the same for every lobby) ---------- */
const CODE_AB = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ';   // no 0/O, 1/I
const LOBBY_HI = 0x01860000n;
let lobby = null, pump = null;
const codeOf = id => { let n = id & 0xffffffffn, s = ''; for (let i = 0; i < 7; i++) { s = CODE_AB[Number(n % 32n)] + s; n /= 32n; } return s; };
const idOf = code => { let n = 0n; for (const ch of String(code).toUpperCase().replace(/[^0-9A-Z]/g, '')) { const v = CODE_AB.indexOf(ch); if (v < 0) return null; n = n * 32n + BigInt(v); } return (LOBBY_HI << 32n) | n; };
const meId = () => { try { return steam.localplayer.getSteamId().steamId64.toString(); } catch (e) { return null; } };
function lobbyInfo() { if (!lobby) return null; let members = []; try { members = lobby.getMembers().map(m => m.steamId64.toString()); } catch (e) {} let owner = null; try { owner = lobby.getOwner().steamId64.toString(); } catch (e) {}
  let myName = ''; try { myName = steam.localplayer.getName(); } catch (e) {}
  return { myName, id: lobby.id.toString(), code: (lobby.id >> 32n) === LOBBY_HI ? codeOf(lobby.id) : lobby.id.toString(), me: meId(), owner, members, names: Object.fromEntries(members.map(m => [m, (() => { try { return steam.friends ? steam.friends.getFriendName ? steam.friends.getFriendName(BigInt(m)) : '' : ''; } catch (e) { return ''; } })()])), data: (() => { try { return lobby.getFullData(); } catch (e) { return {}; } })() }; }
function startPump() { if (pump) return; pump = setInterval(() => { if (!steam || !win) return;
    try { for (let k = 0; k < 200; k++) { const n = steam.networking.isP2PPacketAvailable(); if (!n) break; const p = steam.networking.readP2PPacket(n); win.webContents.send('mp-msg', p.steamId.steamId64.toString(), p.data.toString('utf8')); } } catch (e) {} }, 8);
  try { steam.callback.register(6 /* P2PSessionRequest */, v => { try { steam.networking.acceptP2PSession(v.remote); } catch (e) {} }); } catch (e) {}
  try { steam.callback.register(5 /* LobbyChatUpdate */, () => { if (win) win.webContents.send('mp-lobby', lobbyInfo()); }); } catch (e) {}
  try { steam.callback.register(4 /* LobbyDataUpdate */, () => { if (win) win.webContents.send('mp-lobby', lobbyInfo()); }); } catch (e) {} }
ipcMain.on('mp-ok', e => { e.returnValue = !!steam; });
ipcMain.handle('mp-host', async (e, max) => { if (!steam) throw new Error('Steam is not running'); startPump(); if (lobby) try { lobby.leave(); } catch (err) {} lobby = await steam.matchmaking.createLobby(2, max || 6); return lobbyInfo(); });
ipcMain.handle('mp-join', async (e, code) => { if (!steam) throw new Error('Steam is not running'); startPump(); const id = /^\d{15,}$/.test(String(code)) ? BigInt(code) : idOf(code); if (id == null) throw new Error('That code is not right'); if (lobby) try { lobby.leave(); } catch (err) {} lobby = await steam.matchmaking.joinLobby(id); return lobbyInfo(); });
ipcMain.handle('mp-info', () => lobbyInfo());
ipcMain.on('mp-leave', () => { if (lobby) try { lobby.leave(); } catch (e) {} lobby = null; });
ipcMain.on('mp-data', (e, k, v) => { try { if (lobby) lobby.setData(String(k), String(v)); } catch (err) {} });
ipcMain.on('mp-send', (e, to, data, reliable) => { if (!steam) return; const buf = Buffer.from(String(data), 'utf8'); const me = meId(); const send = id => { try { steam.networking.sendP2PPacket(BigInt(id), reliable || buf.length > 1100 ? 2 : 0, buf); } catch (err) {} };
  if (to === '*') { const info = lobbyInfo(); (info ? info.members : []).forEach(m => { if (m !== me) send(m); }); } else send(to); });

app.whenReady().then(create);
app.on('window-all-closed', () => app.quit());
