"""One-off: where all three levels run nearly the same code and differ only in a few values, keep one shared copy
of the code with @@S:name@@ placeholders, and put each level's values in src/levels/<level>.txt.

python3 tools/merge_settings.py [--dry]
"""
import difflib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS = ['plains', 'gully', 'escarpment']
TOK = re.compile(r'[\w.$]')
# a value that is a setting, not a piece of code: a number or list of numbers, a colour, a word, a quoted string
CLEAN = re.compile(r"-?[\d.]+(?:\s*,\s*-?[\d.]+)*|0x[0-9a-fA-F]+|[0-9a-fA-F]{6}|[A-Za-z][\w ]{0,30}|'[^'\\]{0,60}'|\"[^\"\\]{0,60}\"")


# the settings, named by hand: (plains, gully, cliffs) values -> name. Groups with any value not named here stay as level blocks.
NAMES = {
    ('Plains', 'Gully', 'Cliffs'): 'titleName',
    ('plains', 'gully', 'cliffs'): 'shownName',
    ('plains', 'gully', 'escarpment'): 'key',
    ('42.5,42.5', '48,48', '37.5,14.5'): 'groundTextureRepeat',
    ('aaa396', '8f8b82', 'aaa396'): 'rockColour',
    ('3540', '3540', '3500'): 'farGroundDepth',
    ('152', '152', '150'): 'farGroundRows',
    ('1770', '1770', '1790'): 'farGroundOffset',
    ('300', '300', 'VH'): 'vistaHeight',
    ('lion', 'thy', 'mega'): 'nativePredator',
    ('2.4', '4', '4'): 'preyHopRate',
    ('0.28', '1.1', '1.1'): 'preyHopRatePerSpeed',
    ('0.12', '0.1', '0.1'): 'preyHopHeightWounded',
    ('0.75', '0.45', '0.45'): 'preyHopHeightMax',
    ('0.18', '0.12', '0.12'): 'preyHopHeight',
    ('0.045', '0.05', '0.05'): 'preyHopHeightPerSpeed',
}


def parse(t):
    L = t.split('\n'); segs = []; i = 0; cur = []
    while i < len(L):
        if L[i].startswith('//@if '):
            if cur: segs.append(('S', cur)); cur = []
            lv = L[i][6:].split(); j = i + 1; body = []
            while not L[j].startswith('//@end'): body.append(L[j]); j += 1
            segs.append(('I', lv, body)); i = j + 1
        else: cur.append(L[i]); i += 1
    if cur: segs.append(('S', cur))
    return segs


def align(p, o):
    """for each index in p: index in o if that char is matched, else None"""
    m = [None] * len(p)
    for a, b, n in difflib.SequenceMatcher(None, p, o, autojunk=False).get_matching_blocks():
        for k in range(n): m[a + k] = b + k
    return m


def gaps3(p, g, e):
    mg, me = align(p, g), align(p, e)
    common = [mg[i] is not None and me[i] is not None for i in range(len(p))]
    # keep monotonic and drop tiny common runs between gaps
    runs, i = [], 0
    while i < len(p):
        j = i
        while j < len(p) and common[j] == common[i]: j += 1
        runs.append([common[i], i, j]); i = j
    changed = True
    while changed:
        changed = False
        for k in range(1, len(runs) - 1):
            c, a, b = runs[k]
            if c and (b - a < 3) and not runs[k - 1][0] and not runs[k + 1][0]:
                for x in range(a, b): common[x] = False
                runs[k - 1][2] = runs[k + 1][2]; del runs[k:k + 2]; changed = True; break
    # widen each gap to whole tokens
    def is_tok(c): return bool(TOK.match(c))
    i = 0; out = []
    while i < len(p):
        if common[i]: i += 1; continue
        a = i
        while i < len(p) and not common[i]: i += 1
        b = i
        while a > 0 and is_tok(p[a - 1]) and common[a - 1]: a -= 1
        while b < len(p) and is_tok(p[b]) and common[b]: b += 1
        out.append([a, b])
    merged = []
    for a, b in out:
        if merged and a <= merged[-1][1]: merged[-1][1] = max(b, merged[-1][1])
        else: merged.append([a, b])
    # map to g and e through the common chars around each gap
    res = []
    for a, b in merged:
        ga = (mg[a - 1] + 1) if a > 0 else 0; ea = (me[a - 1] + 1) if a > 0 else 0
        gb = mg[b] if b < len(p) else len(g); eb = me[b] if b < len(p) else len(e)
        if a > 0 and (mg[a - 1] is None or me[a - 1] is None): return None
        if b < len(p) and (mg[b] is None or me[b] is None): return None
        res.append((a, b, ga, gb, ea, eb))
    # check reconstruction
    def rebuild(src, idx):
        s, last = [], 0
        for r in res: s.append(src[last:r[idx]]); s.append('\0'); last = r[idx + 1]
        s.append(src[last:]); return ''.join(s)
    sk = rebuild(p, 0)
    if rebuild(g, 2) != sk or rebuild(e, 4) != sk: return None
    return sk, [(p[a:b], g[ga:gb], e[ea:eb]) for a, b, ga, gb, ea, eb in res]


def name_for(before, vals, used):
    m = re.search(r'([A-Za-z_$][\w$]*)\s*(?:[:=]|\+=|\*=)\s*[^;,{}()]{0,12}$', before[-60:])
    if vals[0] in ('plains', "'plains'", 'Plains', 'PLAINS') or vals == ('plains', 'gully', 'escarpment'): base = 'levelKey'
    elif m: base = m.group(1)
    else:
        m2 = re.search(r'([A-Za-z_$][\w$]*)\W*$', before[-40:])
        base = (m2.group(1) if m2 else 'v')
    base = re.sub(r'\W', '', base)[:24] or 'v'
    return base


def main(dry):
    path = ROOT + '/src/engine.html'
    segs = parse(open(path).read())
    out, vals, used, n_merged, skipped = [], {lv: {} for lv in LEVELS}, {}, 0, 0
    i = 0
    while i < len(segs):
        if segs[i][0] == 'S': out.extend(segs[i][1]); i += 1; continue
        j = i
        while j < len(segs) and segs[j][0] == 'I': j += 1
        grp = segs[i:j]
        per = ['\n'.join(sum([s[2] for s in grp if lv in s[1]], [])) for lv in LEVELS]
        ok = False
        if all(per) and sum(map(len, per)) < 60000 and '/*@' not in ''.join(per).replace('/*@Y*/', '').replace('/*@y*/', '').replace('/*@{y*/', ''):
            r = min(difflib.SequenceMatcher(None, per[a], per[b], autojunk=False).ratio() for a, b in [(0, 1), (0, 2), (1, 2)])
            if r > 0.8:
                res = gaps3(*per)
                if res:
                    sk, diffs = res
                    if all(CLEAN.fullmatch(v) for d in diffs for v in d) and all(NAMES.get(d) for d in diffs):
                        parts = sk.split('\0'); text = parts[0]
                        for k, d in enumerate(diffs):
                            # same three values seen before: same name
                            nm = NAMES[d]
                            for lv, v in zip(LEVELS, d): vals[lv][nm] = v
                            text += '@@S:%s@@' % nm + parts[k + 1]
                        out.extend(text.split('\n')); ok = True; n_merged += 1
        if not ok:
            skipped += 1
            for s in grp: out.append('//@if ' + ' '.join(s[1])); out.extend(s[2]); out.append('//@end')
        i = j
    print('merged groups', n_merged, 'kept as level blocks', skipped, 'values', len(vals['plains']))
    if dry:
        for k in vals['plains']: print('  %-18s %s | %s | %s' % (k, vals['plains'][k][:40], vals['gully'][k][:40], vals['escarpment'][k][:40]))
        return
    open(path, 'w').write('\n'.join(out))
    os.makedirs(ROOT + '/src/levels', exist_ok=True)
    names = {'plains': 'the plains', 'gully': 'the gully', 'escarpment': 'the cliffs'}
    for lv in LEVELS:
        lines = ['# %s: values the shared engine code takes for this level.' % names[lv],
                 '# Each is written into the code where engine.html says @@S:name@@, exactly as given here',
                 '# (so text in quotes keeps its quotes). A value wrapped in ⟦ ⟧ has spaces at its ends.', '']
        for k, v in vals[lv].items():
            lines.append('%s = %s' % (k, ('⟦%s⟧' % v) if v != v.strip() or v == '' else v))
        open(ROOT + '/src/levels/%s.txt' % lv, 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main('--dry' in sys.argv)
