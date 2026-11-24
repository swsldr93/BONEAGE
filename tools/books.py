"""Books, letters, scrolls and maps as plain text files (src/books/), turned back into the game's book library at build time.

A book file:

    title: The Two Collapses
    kind: book                      book / letter / scroll / map
    style: print                    print / hand
    cover: @json 4675414            a value that is not plain text is written @json ...
    coverImg: @file history-cover.jpg   pictures sit in src/books/img/
    pages: below                    where the pages go among these settings (keep the line)
    id: history
    ====
    == h
    The Two Collapses
    == t
    A paragraph of text.
    It can run over several lines.
    == pb                           page break
    == t
    A handwritten line
    -- hand                         a further setting on the same block; no value means 1
    == smap
    @file smP-1.jpg
    -- t
    The note beside the map.
    -- sg
    —2/0 Kel Rus

Block kinds used: t (text), h / h3 (headings), d (date line), s (signature), lat (latin name), pb (page break),
pbl (page break to a left page), stamp, flag, img/bplate/fplate/cpl (pictures), chk (checklist row),
mp (place map page), mnote/mfront (old map note and front), smap (start map with note).
src/books/_order.txt lists the books in library order.
"""
import base64, json, os, re

IMG = re.compile(r'^data:image/(jpeg|webp|png|gif);base64,(.*)$', re.S)
EXT = {'jpeg': 'jpg', 'webp': 'webp', 'png': 'png', 'gif': 'gif'}
MIME = {'jpg': 'jpeg', 'webp': 'webp', 'png': 'png', 'gif': 'gif'}


def _val_out(v, d, name, n):
    if isinstance(v, str):
        m = IMG.match(v)
        if m:
            fn = '%s-%d.%s' % (name, n[0], EXT[m.group(1)]); n[0] += 1
            open(os.path.join(d, 'img', fn), 'wb').write(base64.b64decode(m.group(2)))
            assert base64.b64encode(base64.b64decode(m.group(2))).decode() == m.group(2)
            return '@file ' + fn
        return v
    if v == 1 and type(v) is int: return None
    return '@json ' + json.dumps(v, ensure_ascii=False)


def _val_in(t, d):
    if t is None: return 1
    if t.startswith('@file '):
        fn = t[6:].strip(); ext = fn.rsplit('.', 1)[1]
        return 'data:image/%s;base64,' % MIME[ext] + base64.b64encode(open(os.path.join(d, 'img', fn), 'rb').read()).decode()
    if t.startswith('@json '): return json.loads(t[6:])
    return t


def write_books(lib, d):
    os.makedirs(os.path.join(d, 'img'), exist_ok=True)
    open(os.path.join(d, '_order.txt'), 'w').write('\n'.join(lib) + '\n')
    for bid, b in lib.items():
        n = [1]; out = []
        for k, v in b.items():
            if k == 'blocks': out.append('pages: below'); continue
            t = _val_out(v, d, bid, n)
            out.append('%s: %s' % (k, '@json 1' if t is None else t))
        out.append('====')
        for bl in b['blocks']:
            for i, (k, v) in enumerate(bl.items()):
                t = _val_out(v, d, bid, n)
                out.append(('== ' if i == 0 else '-- ') + k)
                if t is not None: out.append(t)
        open(os.path.join(d, bid + '.txt'), 'w').write('\n'.join(out) + '\n')


def read_books(d):
    lib = {}
    for bid in open(os.path.join(d, '_order.txt')).read().split():
        lines = open(os.path.join(d, bid + '.txt')).read().split('\n')
        if lines and lines[-1] == '': lines.pop()
        sep = lines.index('====')
        b = {}
        for L in lines[:sep]:
            k, v = L.split(': ', 1)
            if k == 'pages': b['blocks'] = []
            else: b[k] = _val_in(v, d)
        cur = None; key = None; buf = None
        def flush():
            if key is not None: cur[key] = _val_in('\n'.join(buf) if buf else None, d)
        for L in lines[sep + 1:]:
            if L.startswith('== ') or L.startswith('-- '):
                flush()
                if L.startswith('== '): cur = {}; b['blocks'].append(cur)
                key = L[3:].strip(); buf = []
            else:
                buf.append(L)
        flush()
        lib[bid] = b
    return lib
