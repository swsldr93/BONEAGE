"""One-off: rebuild an editable source tree from a published web build (index.html, pool.js, pg-*.js).

python3 tools/unpack.py <build-dir> <src-dir>
"""
import json, os, re, sys, difflib

LEVELS = ['plains', 'gully', 'escarpment']
GEN0, GEN1 = '/*@@GEN0@@*/', '/*@@GEN1@@*/'
GENAT = re.compile(r'^;window\.__BA_GENAT=(\d+);if\(performance\.now\(\)>__BA_GENDL\)yield;$')
YC = 'if(!(++__yc&15)&&performance.now()>__BA_GENDL)yield;'


def jstr_at(d, key):
    """decode the JSON value assigned right after `key` in file text d; returns (value, start, end)"""
    i = d.index(key) + len(key)
    v, n = json.JSONDecoder().raw_decode(d[i:])
    return v, i, i + n


def ins_marker(t):
    m = GENAT.match(t)
    if m: return '/*@Y*/'          # numbered 2,3,4... in order by the build
    if t == YC: return '/*@y*/'
    if t == '{' + YC: return '/*@{y*/'
    return '/*@+' + t + '+@*/'


def mark_gen(s, ins):
    """put the generator's yield insertions into the text as markers (applied in list order, as the loader does)"""
    a = s.index(GEN0) + len(GEN0); b = s.index(GEN1)
    g = s[a:b]
    spans = []                            # [start, text] of every insertion, in the growing string
    for o, t in ins:                      # exactly as the loader applies them
        for sp in spans:
            if sp[0] < o < sp[0] + len(sp[1]): raise ValueError('insertion inside an earlier insertion')
            if sp[0] >= o: sp[0] += len(t)
        g = g[:o] + t + g[o:]
        spans.append([o, t])
    spans.sort()
    out, last = [], 0
    for st, t in spans:
        out.append(g[last:st]); out.append(ins_marker(t)); last = st + len(t)
    out.append(g[last:])
    return s[:a] + ''.join(out) + s[b:]


def final_gen(s, ins):
    """what the loader ends up running: the generator text with its insertions applied"""
    a = s.index(GEN0) + len(GEN0); b = s.index(GEN1)
    g = s[a:b]
    for o, t in ins: g = g[:o] + t + g[o:]
    return g


def merge(seqs):
    """three-way line merge: list of (line, set_of_levels) in a common order"""
    items = [(l, {LEVELS[0]}) for l in seqs[0]]
    for lv, lines in zip(LEVELS[1:], seqs[1:]):
        sm = difflib.SequenceMatcher(None, [x[0] for x in items], lines, autojunk=False)
        out = []
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == 'equal':
                for k in range(i2 - i1):
                    l, st = items[i1 + k]; out.append((l, st | {lv}))
            else:
                out.extend(items[i1:i2])
                out.extend((l, {lv}) for l in lines[j1:j2])
        items = out
    return items


def emit(items):
    out, cur = [], None
    full = set(LEVELS)
    for l, st in items:
        key = None if st == full else tuple(x for x in LEVELS if x in st)
        if key != cur:
            if cur is not None: out.append('//@end\n')
            if key is not None: out.append('//@if ' + ' '.join(key) + '\n')
            cur = key
        out.append(l if l.endswith('\n') else l + '\n//@nonl\n')
    if cur is not None: out.append('//@end\n')
    return ''.join(out)


def main(bd, sd):
    os.makedirs(sd + '/pool', exist_ok=True)
    # pool
    p = open(bd + '/pool.js').read()
    pool, _, e1 = jstr_at(p, 'window.BA_POOL=')
    asg, _, e2 = jstr_at(p, 'window.BA_POOLASG=')
    names = []
    for i, c in enumerate(pool):
        m = re.match(r'\s*/\*\s*([^*]{0,60})', c)
        stem = re.sub(r'[^a-z0-9]+', '-', (m.group(1) if m else 'chunk').lower()).strip('-')[:40] or 'chunk'
        fn = '%02d-%s.txt' % (i, stem)
        open(sd + '/pool/' + fn, 'w').write(c); names.append(fn)
    json.dump({'files': names, 'assign': asg}, open(sd + '/pool/index.json', 'w'), indent=1)
    # levels
    seqs = []
    for k in LEVELS:
        d = open(bd + '/pg-%s.js' % k).read()
        s, _, _ = jstr_at(d, 'BA_PGLV.%s=' % k)
        G, _, _ = jstr_at(d, 'BA_PGGEN.%s=' % k)
        seqs.append(mark_gen(s, G['ins']).splitlines(keepends=True))
    open(sd + '/engine.html', 'w').write(emit(merge(seqs)))
    # launcher
    open(sd + '/launcher.html', 'w').write(open(bd + '/index.html').read())


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
