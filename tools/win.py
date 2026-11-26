"""The Windows (x64) desktop build: the same desktop page as the Mac one, in Electron for Windows.

Called by tools/build.py --win. Downloads (once, into tools/cache/) the Electron runtime for Windows at the same version
as the Mac shell, and the Steam library package for its Windows files. Output: out/BoneAge-Windows-x64.zip
(unzip, run "Bone Age.exe").

Not done here: the .exe's own icon and version details (that needs rcedit, a Windows tool); the window icon is set.
"""
import json, os, shutil, subprocess, urllib.request, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESK = ROOT + '/src/desktop'
CACHE = ROOT + '/tools/cache'
ELECTRON = '33.4.11'          # same as the Mac shell (v65)
STEAMWORKS = '0.4.0'


def fetch(url, fn):
    os.makedirs(CACHE, exist_ok=True); p = os.path.join(CACHE, fn)
    if not os.path.exists(p):
        subprocess.run(['curl', '-sSfL', '-o', p + '.part', url], check=True); os.rename(p + '.part', p)
    return p


def build(page_html, out):
    ez = fetch('https://github.com/electron/electron/releases/download/v%s/electron-v%s-win32-x64.zip' % (ELECTRON, ELECTRON), 'electron-v%s-win32-x64.zip' % ELECTRON)
    if not os.path.exists(os.path.join(CACHE, 'steamworks.js-%s.tgz' % STEAMWORKS)):
        subprocess.run(['npm', 'pack', 'steamworks.js@' + STEAMWORKS], cwd=CACHE, check=True, capture_output=True)
    work = out + '/win-work'; shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    app = work + '/Bone Age'
    zipfile.ZipFile(ez).extractall(app)
    os.rename(app + '/electron.exe', app + '/Bone Age.exe')
    for f in ('resources/default_app.asar',):
        if os.path.exists(os.path.join(app, f)): os.remove(os.path.join(app, f))
    # the app archive: the desktop page and start-up, and the Steam library with its Windows files
    src = work + '/asar'; os.makedirs(src)
    shutil.copytree(DESK + '/app', src + '/app')
    shutil.copy(DESK + '/package.json', src + '/package.json')
    sw = work + '/sw'; os.makedirs(sw)
    subprocess.run(['tar', 'xzf', os.path.join(CACHE, 'steamworks.js-%s.tgz' % STEAMWORKS), '-C', sw], check=True)
    os.makedirs(src + '/node_modules', exist_ok=True)
    shutil.copytree(sw + '/package', src + '/node_modules/steamworks.js')
    for d in ('osx', 'linux64'):   # only Windows' own files go in
        shutil.rmtree(src + '/node_modules/steamworks.js/dist/' + d, ignore_errors=True)
    open(src + '/app/index.html', 'w').write(page_html)
    subprocess.run(['node', ROOT + '/tools/node/asar.js', 'pack', src, app + '/resources/app.asar'], check=True, capture_output=True)
    z = out + '/BoneAge-Windows-x64.zip'
    if os.path.exists(z): os.remove(z)
    subprocess.run(['zip', '-qry', z, 'Bone Age'], cwd=work, check=True)
    shutil.rmtree(work)
    return z
