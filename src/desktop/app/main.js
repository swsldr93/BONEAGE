// Bone Age: desktop wrapper for Steam (Electron).
const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const fs = require('fs');

// Steam sets SteamAppId when it launches the game. FALLBACK_APP_ID is only used when you run the exe directly while testing.
const FALLBACK_APP_ID = 0; // put your Steam App ID here for testing outside Steam (0 = no Steam features)
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

app.whenReady().then(create);
app.on('window-all-closed', () => app.quit());
