"""The three peoples' figures: src/people/<people>.glb (as made: rigged, with walk, run, idle, sneak, thrust and throw)
slimmed for the game (finger and toe tracks dropped, walk/run/sneak made to stay in place, keys halved, rotations packed,
idle cut to six seconds, texture recompressed) and written into src/pool/21-people.txt as window.__HUMANS.

python3 tools/people.py
"""
import base64, json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT + '/tools')
import slim
d = {}
for k in ('bassia', 'torresian', 'eromangan'):
    out = tempfile.mktemp(suffix='.glb'); slim.slim(ROOT + '/src/people/%s.glb' % k, out, 2); d[k] = base64.b64encode(open(out, 'rb').read()).decode(); os.remove(out)
open(ROOT + '/src/pool/21-people.txt', 'w').write("/* the three peoples' figures (Bassian, Torresian, Eromangan): skinned models with their walk, run, idle, sneak, thrust and throw */ window.__HUMANS=" + json.dumps(d) + ';')
print('written src/pool/21-people.txt')
