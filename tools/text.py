"""Game text kept in src/text/*.txt and put into the engine at build time.

In src/engine.html a placeholder @@T:<file>:<name>@@ stands for one piece of text; the build replaces it with the
JavaScript string the game uses.

Text file format (src/text/tutorial.txt and others):
    lines starting with # are notes and are ignored
    == name         starts an entry; the lines after it are its text
    [attack]        the key or button for that action, shown in the player's own controls
    {PREY()}        something the game fills in (here: kangaroos or wallabies)
    a blank line    a new paragraph (on screen: a gap between paragraphs)
"""
import os, re

SEG = re.compile(r"\[(\w+)\]|\{([^{}]+)\}")


def _lit(s):
    return "'" + s.replace('\n\n', '<br><br>') + "'"


def to_js(text):
    """entry text -> the JavaScript expression"""
    parts, last = [], 0
    for m in SEG.finditer(text):
        if m.start() > last: parts.append(_lit(text[last:m.start()]))
        parts.append("b('%s')" % m.group(1) if m.group(1) else m.group(2))
        last = m.end()
    if last < len(text) or not parts: parts.append(_lit(text[last:]))
    return '+'.join(parts)


def from_js(expr):
    """JavaScript expression of quoted pieces and calls joined by + -> entry text (inverse of to_js)"""
    out, i = [], 0
    while i < len(expr):
        if expr[i] == "'":
            j = expr.index("'", i + 1)
            lit = expr[i + 1:j]
            assert '\\' not in lit and '[' not in lit and '{' not in lit and '\n' not in lit, lit
            out.append(lit.replace('<br><br>', '\n\n')); i = j + 1
        else:                                     # code up to the next + outside quotes and brackets
            j, depth, q = i, 0, None
            while j < len(expr):
                c = expr[j]
                if q:
                    if c == q: q = None
                elif c in "'\"": q = c
                elif c in '([': depth += 1
                elif c in ')]': depth -= 1
                elif c == '+' and depth == 0: break
                j += 1
            e = expr[i:j]
            assert '{' not in e and '}' not in e, e
            m = re.fullmatch(r"b\('(\w+)'\)", e)
            out.append('[%s]' % m.group(1) if m else '{%s}' % e); i = j
        if i < len(expr):
            assert expr[i] == '+', expr[i:i + 20]; i += 1
    return ''.join(out)


def read(path):
    ent, name, buf = {}, None, []
    for L in open(path).read().split('\n'):
        if L.startswith('#'): continue
        if L.startswith('== '):
            if name: ent[name] = '\n'.join(buf).strip('\n')
            name, buf = L[3:].strip(), []
        else: buf.append(L)
    if name: ent[name] = '\n'.join(buf).strip('\n')
    return ent


def expand(engine, d):
    cache = {}
    def rep(m):
        f, k = m.group(1), m.group(2)
        if f not in cache: cache[f] = read(os.path.join(d, f + '.txt'))
        if k not in cache[f]: raise SystemExit('text %s.txt has no entry "%s"' % (f, k))
        return to_js(cache[f][k])
    def rep_obj(m):   # @@TOBJ:<file>@@ -> {name:'text',...} with every entry of the file, in order
        f = m.group(1)
        if f not in cache: cache[f] = read(os.path.join(d, f + '.txt'))
        return '{' + ','.join('%s:%s' % (k, to_js(v)) for k, v in cache[f].items()) + '}'
    engine = re.sub(r'@@TOBJ:(\w+)@@', rep_obj, engine)
    return re.sub(r'@@T:(\w+):([\w.]+)@@', rep, engine)
