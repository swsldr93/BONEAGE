# Bone Age

A first-person survival game set in far-future Australia. © 2026 Matthew Treacey.

## Building

    python3 tools/build.py                 web build into out/web (index.html, pool.js, pg-*.js)
    python3 tools/build.py --mac           also the Mac (Apple Silicon) app: out/BoneAge-Mac-AppleSilicon.zip
    python3 tools/build.py --win           also the Windows (x64) app: out/BoneAge-Windows-x64.zip
    python3 tools/build.py --check DIR     also compare with a published build in DIR ("IDENTICAL GAME" or not)

The Mac build needs `node`, `npm install` in `tools/node`, `rcodesign` (set `RCODESIGN=/path/to/rcodesign` if it
is not on the path) and a Mac shell zip: any earlier Bone Age Mac zip. Only its Electron framework and Steam
library are used. See `tools/mac.py`.

## Branches

- `survival`: Bone Age Survival, for test players. No warfare.
- `main`: Bone Age X, the game with warfare, where work goes on. Fixes to the shared game are made on `main` and brought into `survival` (git cherry-pick), leaving warfare out.

## Where things are

| Path | What |
|---|---|
| `src/launcher.html` | the menu and level loader (the web build's index.html); `@@VER@@` is the build's version mark |
| `src/engine.html` | the game: every level's page in one file. Code between `//@if plains gully` and `//@end` goes only into the levels named; everything else is shared |
| `src/levels/*.txt` | each level's values for shared code (`@@S:name@@` in engine.html): name, predator, ground texture, prey hop, the fort's flag… (`escarpment` = the cliffs). A value `@file img/x.jpg` is a picture in `src/levels/img/` |
| `src/books/*.txt` | every book, letter, scroll and map, as text. Pictures in `src/books/img/`. Format: top of `tools/books.py` |
| `src/text/*.txt` | tutorial pages and place names (`@@T:file:name@@` / `@@TOBJ:file@@` in engine.html). Format: top of `tools/text.py` |
| `src/pool/` | shared chunks (code, models, sounds) the levels load as `@@Pn@@`; `index.json` lists them |
| `src/desktop/` | the Mac app: Electron start-up (`app/main.js`, `preload.js`), fonts, three.js, and the higher-quality skins, bird models and ambience used only on desktop |
| `tools/` | build, Mac build, book and text converters; `unpack.py` and `merge_settings.py` were used once to recover this source from the v70 build |

## Level generation pauses

Inside the level generator (between `/*@@GEN0@@*/` and `/*@@GEN1@@*/` in engine.html) the markers `/*@Y*/`,
`/*@y*/`, `/*@{y*/` and `/*@+text+@*/` are the points where generation may pause for a frame so the game does not
freeze while a level is built. The build numbers them and hands them to the loader. After any new slow top-level
step in the generator, add `/*@Y*/`.

## History

The original engine source was lost on 25 Nov 2026 when the work environment was reset. This tree was rebuilt
from the published v70 build; `tools/build.py --check` against v70 gives `IDENTICAL GAME`.
