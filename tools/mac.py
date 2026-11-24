"""The Mac (Apple Silicon) desktop build, made from the same web build.

Called by tools/build.py --mac. Needs:
  - a Mac shell: an earlier Bone Age Mac zip (Electron, the Steam library); only its framework and Steam library
    are used, everything of the game is replaced. Default: the v65 zip kept in the outputs backup.
  - node (for the app archive) and rcodesign (ad-hoc signing, so Apple Silicon will open it)

What the desktop page differs in from the web one:
  - fonts load from the app (fonts/fonts.css) instead of Google
  - three.js comes from the app instead of the CDN (window.__BA_THREESRC)
  - the pool and the three levels are written into the page, nothing is fetched
  - higher quality predator skins, prey skins, bird models and ambience (src/desktop/hq-*)
"""
import json, os, plistlib, re, shutil, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESK = ROOT + '/src/desktop'
SHELL = '/mnt/user-data/outputs/bone-age-backup/BoneAge-Mac-AppleSilicon-v65.zip'
FONT_LINKS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
              '<link href="https://fonts.googleapis.com/css2?family=Alegreya:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">\n')
FONT_LOCAL = '<link href="fonts/fonts.css" rel="stylesheet">\n'
THREE_CDN = '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'
THREE_LOCAL = '<script>(function(){ var w=window; while(w!==w.parent&&!w.__BA_THREESRC) w=w.parent; (0,window.eval)(w.__BA_THREESRC); })();</script>'
BOOKFONT = "'https://fonts.googleapis.com/css2?family=Caveat:wght@500&display=swap'"


def once(s, a, b, what):
    n = s.count(a)
    if n != 1: raise SystemExit('mac build: expected one %s, found %d' % (what, n))
    return s.replace(a, b)


def level(s):
    s = once(s, FONT_LINKS, FONT_LOCAL, 'font links in a level')
    s = once(s, THREE_CDN, THREE_LOCAL, 'three.js script in a level')
    loc = "'fonts/fonts.css?v="; loc += '0' * (len(BOOKFONT) - len(loc) - 1) + "'"   # same length: the generator's pause points stay put
    return once(s, BOOKFONT, loc, 'book font link')


def page(files, levels, jdump):
    pool = json.loads(files['pool.js'][len('window.BA_POOL='):files['pool.js'].index(';\nwindow.BA_POOLASG=')])
    hqm = json.load(open(DESK + '/hq-models.json'))
    i = [k for k, c in enumerate(pool) if c.startswith('window.__GBM=')]
    if len(i) != 1: raise SystemExit('mac build: bird model chunk not found')
    web = json.loads(pool[i[0]][len('window.__GBM='):-1])
    if set(web) != set(hqm): print('WARNING: desktop bird models differ from the web set:', sorted(set(web) ^ set(hqm)), '(using web ones for those)')
    pool[i[0]] = 'window.__GBM=' + json.dumps({k: hqm.get(k, v) for k, v in web.items()}) + ';'
    asg = files['pool.js'][files['pool.js'].index('window.BA_POOLASG='):]
    inline = 'window.BA_POOL=' + jdump(pool) + ';\n' + asg + '\n'
    for lv, (s, ins) in levels.items():
        inline += ('window.BA_PGLV=window.BA_PGLV||{}; BA_PGLV.%s=' % lv + jdump(level(s)) +
                   '; window.BA_PGGEN=window.BA_PGGEN||{}; BA_PGGEN.%s=' % lv + json.dumps({'ins': ins}, separators=(',', ':')) + ';\n')
    L = files['index.html']
    L = once(L, FONT_LINKS, FONT_LOCAL, 'font links in the launcher')
    L = re.sub(r'<script src="pool\.js\?v=\w+"></script>', lambda m: '<script>' + inline + '</script>', L)
    m = re.search(r'window\.__BA_AMB=', L); j = m.end()
    amb, n = json.JSONDecoder().raw_decode(L[j:])
    hqa = json.load(open(DESK + '/hq-ambience.json'))
    L = L[:j] + json.dumps({k: hqa.get(k, v) for k, v in amb.items()}) + L[j + n:]
    head = open(DESK + '/hq-skins.html').read() + '<script>window.__BA_THREESRC=' + jdump(open(DESK + '/app/three.min.js').read()) + ';</script>\n'
    return once(L, '<head>\n', '<head>\n' + head, 'head in the launcher')


def build(files, levels, jdump, out, shell=SHELL, rcodesign='rcodesign'):
    work = out + '/mac-work'; shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    subprocess.run(['unzip', '-q', shell, '-d', work + '/shell'], check=True)
    app = [d for d in os.listdir(work + '/shell') if d.endswith('.app')][0]
    APP = work + '/shell/' + app
    res = APP + '/Contents/Resources'
    nodejs = ROOT + '/tools/node/asar.js'
    subprocess.run(['node', ROOT + '/tools/node/node_modules/@electron/asar/bin/asar.js', 'extract', res + '/app.asar', work + '/old'], check=True)
    src = work + '/asar'; os.makedirs(src)
    shutil.copytree(DESK + '/app', src + '/app', ignore=shutil.ignore_patterns('*.json.tmp'))
    shutil.copy(DESK + '/package.json', src + '/package.json')
    shutil.copytree(work + '/old/node_modules', src + '/node_modules')
    open(src + '/app/index.html', 'w').write(page(files, levels, jdump))
    os.remove(res + '/app.asar'); shutil.rmtree(res + '/app.asar.unpacked', ignore_errors=True)
    h = subprocess.run(['node', nodejs, 'pack', src, res + '/app.asar'], check=True, capture_output=True, text=True).stdout.strip()
    pl = APP + '/Contents/Info.plist'
    p = plistlib.load(open(pl, 'rb')); p['ElectronAsarIntegrity']['Resources/app.asar']['hash'] = h
    plistlib.dump(p, open(pl, 'wb'))
    subprocess.run([rcodesign, 'sign', APP], check=True, capture_output=True)
    z = out + '/BoneAge-Mac-AppleSilicon.zip'
    if os.path.exists(z): os.remove(z)
    subprocess.run(['zip', '-qry', z, app], cwd=work + '/shell', check=True)
    shutil.rmtree(work)
    return z
