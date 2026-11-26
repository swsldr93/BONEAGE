"""Build the web game from src/ into out/web/.

python3 tools/build.py            build
python3 tools/build.py --check D  also compare against a published build in folder D
python3 tools/build.py --mac      also make the Mac app zip in out/ (see tools/mac.py)
python3 tools/build.py --win      also make the Windows app zip in out/ (see tools/win.py)

Source layout
  src/launcher.html      the menu / loader page (index.html of the web build)
  src/engine.html        every level's page in one file. Lines between
                           //@if plains gully
                           ...
                           //@end
                         go only into the levels named. //@nonl marks a line that has no line break at its end.
                         Inside the level generator (between /*@@GEN0@@*/ and /*@@GEN1@@*/) the markers
                           /*@Y*/  /*@y*/  /*@{y*/  /*@+text+@*/
                         are the points where level generation may pause for a frame; the build turns them
                         into the loader's insertion list. Put a /*@Y*/ after any new slow top-level step.
  src/pool/              shared chunks (code, models, sounds, books) used by several levels as @@Pn@@
  src/pool/index.json    chunk order and which globals each chunk sets
  src/books/             every book, letter, scroll and map as a text file (see tools/books.py); the build puts
                         them into src/pool/04-books.txt where it says @@BOOKLIB@@
  src/levels/<level>.txt each level's values for the shared code, put in where engine.html says @@S:name@@
  src/text/              other game text (tutorial pages, place names), put into engine.html where it says
                         @@T:file:name@@ or @@TOBJ:file@@ (see tools/text.py)
"""
import hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS = ['plains', 'gully', 'escarpment']
GEN0, GEN1 = '/*@@GEN0@@*/', '/*@@GEN1@@*/'
YC = 'if(!(++__yc&15)&&performance.now()>__BA_GENDL)yield;'
MARK = re.compile(r'/\*@(Y|y|\{y|\+(.*?)\+@)\*/', re.S)


def level_text(engine, lv):
    out, on, stack = [], True, []
    for line in engine.splitlines(keepends=True):
        if line.startswith('//@if '):
            stack.append(on); on = on and lv in line[6:].split(); continue
        if line.startswith('//@end'):
            on = stack.pop(); continue
        if line.startswith('//@nonl'):
            if on and out and out[-1].endswith('\n'): out[-1] = out[-1][:-1]
            continue
        if on: out.append(line)
    if stack: raise SystemExit('engine.html: //@if without //@end')
    return ''.join(out)


def settings(s, path):
    """put this level's values (src/levels/<level>.txt) where the shared code says @@S:name@@"""
    vals = {}
    for L in open(path).read().split('\n'):
        if not L.strip() or L.startswith('#'): continue
        k, v = L.split(' = ', 1)
        if v.startswith('⟦') and v.endswith('⟧'): v = v[1:-1]
        if v.startswith('@file '):   # a picture beside the sheet (src/levels/img/...), written in as a data URI
            import base64
            fn = os.path.join(os.path.dirname(path), v[6:].strip()); ext = fn.rsplit('.', 1)[1].lower()
            v = 'data:image/%s;base64,' % ('jpeg' if ext in ('jpg', 'jpeg') else ext) + base64.b64encode(open(fn, 'rb').read()).decode()
        vals[k.strip()] = v
    def rep(m):
        if m.group(1) not in vals: raise SystemExit('%s has no value "%s"' % (os.path.basename(path), m.group(1)))
        return vals[m.group(1)]
    return re.sub(r'@@S:(\w+)@@', rep, s)


def split_gen(s):
    """take the pause markers out of the generator; return clean text and the loader's insertion list"""
    a = s.index(GEN0) + len(GEN0); b = s.index(GEN1)
    g, clean, ins, last, n = s[a:b], [], [], 0, 2
    pos = 0
    for m in MARK.finditer(g):
        clean.append(g[last:m.start()]); pos += m.start() - last; last = m.end()
        k = m.group(1)
        if k == 'Y': t = ';window.__BA_GENAT=%d;if(performance.now()>__BA_GENDL)yield;' % n; n += 1
        elif k == 'y': t = YC
        elif k == '{y': t = '{' + YC
        else: t = m.group(2)
        ins.append([pos, t])
    clean.append(g[last:])
    ins.reverse()                    # applied in order: from the end back, so offsets stay true
    return s[:a] + ''.join(clean) + s[b:], ins


def final_gen(s, ins):
    a = s.index(GEN0) + len(GEN0); b = s.index(GEN1)
    g = s[a:b]
    for o, t in ins: g = g[:o] + t + g[o:]
    return g


def jdump(v): return json.dumps(v).replace('</', '<\\/')


def build(out):
    os.makedirs(out, exist_ok=True)
    src = ROOT + '/src'
    sys.path.insert(0, ROOT + '/tools'); import text
    engine = text.expand(open(src + '/engine.html').read(), src + '/text')
    levels = {}
    for lv in LEVELS:
        s, ins = split_gen(settings(level_text(engine, lv), src + '/levels/%s.txt' % lv))
        levels[lv] = (s, ins)
    idx = json.load(open(src + '/pool/index.json'))
    pool = [open(src + '/pool/' + f).read() for f in idx['files']]
    sys.path.insert(0, ROOT + '/tools'); import books
    lib = json.dumps(books.read_books(src + '/books'))
    pool = [c.replace('@@BOOKLIB@@', lib) for c in pool]
    files = {'pool.js': 'window.BA_POOL=' + jdump(pool) + ';\nwindow.BA_POOLASG=' + json.dumps(idx['assign'], separators=(',', ':')) + ';\n'}
    for lv, (s, ins) in levels.items():
        files['pg-%s.js' % lv] = ('window.BA_PGLV=window.BA_PGLV||{}; BA_PGLV.%s=' % lv + jdump(s) +
                                  '; window.BA_PGGEN=window.BA_PGGEN||{}; BA_PGGEN.%s=' % lv + json.dumps({'ins': ins}, separators=(',', ':')) + ';')
    ver = hashlib.sha1(''.join(files[k] for k in sorted(files)).encode()).hexdigest()[:10]
    files['index.html'] = open(src + '/launcher.html').read().replace('@@VER@@', ver)   # a new build: maps and layouts drawn by an older one are redrawn
    for k, v in files.items(): open(os.path.join(out, k), 'w').write(v)
    return files, levels


def check(files, levels, ref):
    """same game as the published build in ref? Pages and pool must match exactly, and each level's
    generator must come out the same once its pauses are put in (the insertion list itself may be written differently)"""
    ok = True
    def jat(d, key):
        i = d.index(key) + len(key); return json.JSONDecoder().raw_decode(d[i:])[0]
    for lv, (s, ins) in levels.items():
        d = open(os.path.join(ref, 'pg-%s.js' % lv)).read()
        rs, rg = jat(d, 'BA_PGLV.%s=' % lv), jat(d, 'BA_PGGEN.%s=' % lv)
        a, b = rs == s, final_gen(rs, rg['ins']) == final_gen(s, ins)
        print('%-11s page %s  generator %s' % (lv, 'same' if a else 'DIFFERENT', 'same' if b else 'DIFFERENT')); ok &= a and b
    p = open(os.path.join(ref, 'pool.js')).read() == files['pool.js']
    print('pool.js     %s' % ('same' if p else 'DIFFERENT')); ok &= p
    def norm(t):   # the page as published carries the host's wrapper, and each build its own version mark
        t = t[t.index('<!DOCTYPE html>\n<html lang="en">'):]
        if t.endswith('</body></html>'): t = t[:-len('</body></html>')]
        v = re.search(r'pool\.js\?v=(\w+)', t).group(1)
        return t.replace(v, 'V')
    l = norm(open(os.path.join(ref, 'index.html')).read()) == norm(files['index.html'])
    print('index.html  %s' % ('same' if l else 'DIFFERENT')); ok &= l
    print('IDENTICAL GAME' if ok else 'NOT IDENTICAL')
    return ok


if __name__ == '__main__':
    files, levels = build(ROOT + '/out/web')
    print('built out/web')
    if '--mac' in sys.argv:
        import mac
        rc = os.environ.get('RCODESIGN', 'rcodesign')
        print('built', mac.build(files, levels, jdump, ROOT + '/out', rcodesign=rc))
    if '--win' in sys.argv:
        import mac, win
        print('built', win.build(mac.page(files, levels, jdump), ROOT + '/out'))
    if '--check' in sys.argv: sys.exit(0 if check(files, levels, sys.argv[sys.argv.index('--check') + 1]) else 1)
