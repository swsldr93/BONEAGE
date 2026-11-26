# Bone Age — handover for a new session

Written 27 Nov 2026 by the session that built most of the current game (versions ~v70 → v94).
Read this whole file before changing anything. Then read `README.md`.

---

## 1. Who you are working with

**Matt Treacey** (Matthew), Sydney, Australia (AEDT, UTC+11). Email/lifecycle marketing consultant by trade; background in
marine biology and ecology; Bone Age is his "dream videogame". He is not a programmer. He plays the builds and reports by
eye and ear.

How he wants you to work (his standing instructions — follow them):

- Be direct and plain. Robot-like (he cites HAL 9000), no flattery, no "great question", no grovelling.
- Tell the truth even when unwelcome. Never make up an answer; say "I don't know" when you don't.
- Do not push him to act. You are a collaborator, not a motivator.
- Limit jargon. Explain in plain words. Define every acronym every time you use it.
- No moralising or scolding.

Things learnt about how he works on this game:

- He judges by looking and listening. **Send screenshots** of anything visual you change, whenever you can take one.
- **Use the game's own assets** (its models, textures, sounds, fonts) rather than inventing new art. When he supplies art
  (flags, figure renders, the skull in his HUD mockup) use it.
- **When a feature is removed, remove its code too.** No dead code left behind.
- He batches many small requests into one message; work through all of them, and say plainly which you could not do or
  could not test.
- He once said "skip tests just go" for a batch of people/NPC work. Default is still to test what you can.
- Code comments in this project are plain-English sentences inside `/* ... */`, describing what the player sees or what the
  code means in the world ("a pack that has picked one of a side and is on them: that side's bots go for it"). Keep that
  voice. Avoid jargon in comments too.
- He rejected a font change (Lora) — the original fonts stay. Do not change fonts without asking.
- Every round ends with: build, publish the web pages, build Mac + Windows zips, send them, back up the source.

---

## 2. The game in one paragraph

First-person survival in far-future Australia. You carry a spear, hunt prey (kangaroos/wallabies, emus, birds, diprotodons
on the plains), avoid or fight predators (thylacines, thylacoleo "marsupial lion", megalania lizard), cook at fires, read
documents/maps, and light fires. Six **places** across three **levels**, two fires per place, **12 fires** in all:

| Place id | Name | Level file |
|---|---|---|
| G1 | the upper gully | `gully` |
| G2 | the lower gully | `gully` (also has the fort village when `ba_npc=fort`) |
| P1 | the high plains | `plains` |
| P2 | the far plains | `plains` |
| C2 | the high forest | `escarpment` (the cliffs) |
| C1 | the east cliffs | `escarpment` |

Each place is generated from a seed (deterministic: same seed → same world). Points of interest (POIs: fort/palisade,
shack, bark hut, hollow log, ruins, woolshed, tank, tower, campsites…) are placed by the generator.

Two products:

- **Bone Age Survival** — survival only, for test players.
- **Bone Age X** — survival + **warfare**: three peoples (Bassians, Torresians, Eromangans; figures in `src/people/`),
  3 against 3 with bots, take and hold fires; quick (one place) / standard (3 places) / long (all 6); and now **online**
  play over Steam.

---

## 3. Where everything is

### Source

- Git repository on GitHub: **`swsldr93/BONEAGE`** (private). At the time of writing it may still be empty: this session
  could not push (its GitHub access was fixed before the repo existed). Matt has `bone-age.bundle` (a git bundle of all
  branches). If the repo is empty, ask Matt to attach `bone-age.bundle`, then:

      git clone bone-age.bundle bone-age && cd bone-age
      git remote set-url origin https://github.com/swsldr93/BONEAGE.git
      git push -u origin --all

- Commit author for this repo: **Matt Treacey <matt@naturalorders.com>** (`git config user.name/user.email`).
- A full source tarball also exists in Matt's downloads as `source-latest.tgz`.

### Branches

| Branch | What | Published to |
|---|---|---|
| `main` | **Bone Age X**: everything, including warfare and online. Where work goes on. | "Bone Age X" artifact |
| `survival` | **Bone Age Survival**: no warfare at all (launcher has no warfare button, warfare code removed, the `flag*` level keys removed). | "Bone Age Survival" artifact |
| `multiplayer` | Old: online was built here, then fast-forwarded into `main`. Safe to delete. | — |

**Rule:** fixes to the shared game are made on `main`, then brought to `survival` with `git cherry-pick` (or by applying
only the shared hunks of a diff with `git apply --3way` when a commit mixes warfare and shared changes). Never bring warfare
code into `survival`.

Handy: keep a second worktree for `survival` so both can be built without switching:
`git worktree add ../survtree survival`.

### Published pages (claude.ai artifacts, all private to Matt — he shares them himself)

| Page | URL | From |
|---|---|---|
| Bone Age X | https://claude.ai/artifact/UbzdcLjzHkrgNx8wtWbdut | `main` `out/web` — at **v94** (web identical to v93) |
| Bone Age Survival | https://claude.ai/artifact/7pE11RHLoiorQpRvcMENiC | `survival` `out/web`, title "Bone Age Survival" |
| Bone Age Online Test | https://claude.ai/artifact/Vy59oQeFBkS59m2sQaYcak | older online build; superseded by Bone Age X. Can be deleted if Matt agrees. |
| Opening Bone Age (doc) | https://claude.ai/artifact/VP7YdtmnJSrfNzctc7dkem | Instructions for testers: opening on Mac, Windows, browser |

Publish a page with its files: `index.html` as the page and `pool.js`, `pg-plains.js`, `pg-gully.js`,
`pg-escarpment.js` as supporting files, passing the existing artifact `url` (read it first in a new session). `pool.js`
must stay **under 16 MB** (it is ~15.8 MB — very little headroom; any new model/texture must be slimmed).

---

## 4. Building

    python3 -I tools/build.py                 # web: out/web/
    python3 -I tools/build.py --mac --win     # + out/BoneAge-Mac-AppleSilicon.zip, out/BoneAge-Windows-x64.zip

Needs (not in git — see `.gitignore`):

- `tools/cache/electron-v33.4.11-win32-x64.zip` (Electron for Windows, from github.com/electron/electron releases)
- `tools/cache/steamworks.js-0.4.0.tgz` (`npm pack steamworks.js@0.4.0`)
- `npm install` in `tools/node` (provides `@electron/asar`)
- **rcodesign** (apple-codesign **0.27.0**, Linux musl build, from github.com/indygreg/apple-platform-rs releases);
  set `RCODESIGN=/path/to/rcodesign`
- **A Mac shell zip**: any earlier Bone Age Mac zip placed at `out/BoneAge-Mac-AppleSilicon.zip`. Only its Electron
  framework and Steam library are reused (`tools/mac.py`). Ask Matt to attach his latest
  `BoneAgeX-Mac-AppleSilicon-v94.zip` if you have none.

`build.py` replaces `@@VER@@`, inlines `@@IMG:path@@` (data URIs from `src/`), fills `@@S:key@@` from `src/levels/*.txt`,
`@@T:..@@` from `src/text`, pool chunks `@@Pn@@`, and the `//@if level ... //@end` blocks in `src/engine.html`.

After building, check syntax:

    node tools/test/syntax.js out/web          # parses every level script; expect "errors 0" for all three
    # launcher scripts: extract each <script> from out/web/index.html and run `node --check` on it

Deliverable naming used so far (in Matt's downloads): `BoneAgeX-Mac-AppleSilicon-v94.zip`,
`BoneAgeX-Windows-x64-v94.zip`, `BoneAgeSurvival-…-v94.zip`. Bump the version number each round.

Matt's machines: Mac (Apple Silicon). Windows builds are for others. macOS needs "Open Anyway" in Privacy & Security
(builds are ad-hoc signed, not notarised); Windows shows SmartScreen "More info → Run anyway". This is written up in the
Opening Bone Age doc.

---

## 5. Testing in a cloud workspace

There is no GPU. Chromium + Playwright with SwiftShader works:

- The **plains** render headless. The **gully and cliffs crash headless rendering** — pause the renderer: replace
  `renderer.render` with a no-op after load (the harnesses do this via `window.__T('renderer')`).
- Use small viewports (480×270 or 640×360). Larger ones render black or crash.
- The harnesses route `pg-*.js` through a loader that injects `window.__T = s => eval(s)` into the level script, so a test
  can read and change any level variable: `fw(page, "state+' '+pl.hp")`.
- `tools/test/war-flow.js "<place name>"` — opens the menu, starts a quick war in that place, presses through the intro,
  reports state, bots and audio levels. Serve `out/web` first: `cd out/web && python3 -m http.server 8765`.
- `tools/test/online-two-windows.js` — two pages in one browser context: host and join by code (BroadcastChannel
  transport), start a war, check players see each other, hits, animal ownership and a forwarded kill. The second window
  runs very slowly (two games on a software renderer); allow 10–25 minutes.
- `tools/test/syntax.js out/web` — syntax check.
- `window.__BA_DBG.sim(n)` exists but breaks the frame loop; prefer real time.
- Headless audio: you can tap the output with an AnalyserNode on the compressor after `A.master` to prove sound is playing.

What could **never** be checked here: the gully and cliffs visually, Steam, real performance.

---

## 6. Code map

### `src/launcher.html` (becomes `out/web/index.html`)

The title, menu (survival → level select; warfare → side panel), map drawing for the network of places, level loading.

- Levels load into **iframes** (`frameLevel`, `BA_PRELOAD`, `__BA_TAKEOVER`). Window properties named `BA_*`, `__BA_*` and
  `BAS` are copied into each level frame.
- `BAS` is the storage wrapper (keys `ba_*`). Important keys: `ba_war` (the war state JSON), `ba_next` (`node:P1` etc.),
  `ba_skip_intro`, `ba_npc` (`fort` turns on the G2 village), `ba_tutoff`, `ba_onb`, `ba_net` (the network of places
  and seeds), `ba_devcode`.
- `playNode(id)` loads a place. `netNew()/netSet()/netGet()` make and store the network of places (seeds per node).
- **Warfare panel** (`#warPick`, built in `pick()`): sits right of the logo (no separate screen). Toggle row
  `offline · host online · join online`; choose people (flags over figure renders on firelit pools, no white panels);
  then how long a war (quick → place / standard / long); `start(k,B,line)` sets `ba_war` and plays `line[0]`. Online: host
  goes to `lobbyView()`, joiners type the code.
- **`window.__BA_NET`** (search for "online: the connection between players"): the network layer.
  Steam in the desktop app (`window.baNative.mp`), or a BroadcastChannel between windows of one browser (test only).
  Holds the lobby (host-owned: players, sides, bots, line), `host()`, `join(code)`, `leave()`, `switchSide()`,
  `setBots()`, `botSplit()`, `send(to,obj,reliable)`. Messages whose type starts with `g` go to the level's handler
  (`__BA_NET.game`); the rest are lobby messages (`hello`, `lobby`, `side`, `start`, `bye`, `full`).
  `window.__BA_FIG` = figure images + skull for the in-game HUD.

### `src/desktop/app/main.js`, `preload.js` (Electron)

- `FALLBACK_APP_ID = 5633130` — Bone Age's Steam app id. Steam partner id 455518.
- Multiplayer bridge: `mp-host` (create Public lobby, max 6), `mp-join` (by code or full id), `mp-send` (P2P packet; reliable
  when asked or large), packet pump every 8 ms, P2P session auto-accept (callback 6), lobby updates (callbacks 4/5).
- **Room code** = lobby id low 32 bits in 7 letters (alphabet without 0/O/1/I), assuming the high 32 bits are `0x01860000`.
  If that assumption is wrong for real lobbies, the code shown is the full numeric id, which also works.
- Outside Steam the signed-in Steam account must **own the app** (Matt's developer account does; a second test account
  needs a developer key from Steamworks → Request Steam Product Keys). Without ownership `ok()` is false and online says
  "Steam is not running".

### `src/engine.html` — the game (one file, all levels)

Very large. Key systems and where to search:

| Search for | What |
|---|---|
| `function frame(now,once)` | the main loop; per-level `if(state==='play')… else if(state==='dying')… else if(state==='spec')… else if(state==='paused')… else if(state==='title')` |
| `function updatePlayer`, `hurtPlayer`, `die(`, `showDeath` | the player |
| `updatePack`, `updateAllPacks`, `packs`, `thyls`, `lions` | predators (packs; plains has several) |
| `updateWallabies`, `updateRoosM`, `updateDips` | prey and diprotodons |
| `hitAnimal`, `killAnimal`, `aliveAnimals` | blows on animals |
| `const GB=(()=>` | ground birds (`window.__GB`) |
| `kind==='fort'` … the POI builders | forts, shack, barkhut, log, ruins, tank, woolshed… inside the generator; `W2(u,v)` maps POI-local to world |
| `POISH`, `inPoiShelter`, `inShelter` | shelters predators cannot reach into (slot rocks + hollow log, shack, bark hut interiors) |
| `/*@@GEN0@@*/ … /*@@GEN1@@*/` | the level generator; seeded `Math.random` from `__PGSEED` |
| `sheetSVG`, `todoSVG`, `__localMapSVG`, `__netMapSVG` | the maps (warfare colours fires by owner via `__mapFire`, `__mapWarKey`, `__mapTodo`) |
| `function pause()` | pause screen: right side shows only place + `fires lit n/2`; with tutorial off the left aims are hidden |
| `const NPCB=(()=>` | **people** (shared by all levels): `humanBody` GLB figures with clips idle/walk/run/sneak/thrust/throw, Verlet ragdoll, bands, `pickTarget`, `seeP` (detection like animals: standing 22 m, walking 32, crouched 8–12, crouched in cover 4–7, sprinting 48, ×0.6 at night), `hurtNpc`, `strike`, `throwAt`, `spearTick`, `spawnAt`, `drop`, `visSpear`. Returns `{tick,list,bands,spears,reset,hurt,spawnBand,callUp,spawnAt,drop,T,visSpear,startAct}` as `window.__NPCB`. |
| `const WAR=(()=>` | **warfare** (X only), `window.__WAR`. See below. |

#### The WAR module (Bone Age X)

- State `ba_war` = `{A,B,own:{place:[owner,owner]},i,line,mp?}`. `LINE` = places of this war; `NEED = LINE.length*2`.
- Two fires per place (`F`, first two valid pits); flagpoles placed clear of roofs/walls/caves (raycasts down for anything
  overhead within 1.3 m, `overlaps` 1.1 m, not in cave passages). All fires burn from the start of a war (`allLit`).
- Capture: stand within 5 m for 10 s with no defender there. A place is won when a side holds no fire there and has no
  one standing. Next place via `nextPlace()` → `ba_next` → `baReload()`.
- Sides: `ME` = your side (`A` offline). Bots: offline A has 2 (slots 1,2), B has 3. Online: players fill slots first in
  each side, bots fill the rest (`MP.bots` per side).
- Bots: hunger and hunting, respawn after **90 s** at a fire of theirs; follow the nearest player of their side in
  formation **ahead-left / ahead-right** (crouch when you crouch); **J** or **d-pad right** calls them back (they drop
  fights for 6 s); they rally on a predator that bites — or **stalks** — one of their side within 30 m; predators pick one
  victim at random (`pack.victim`) and rest 60–120 s after; a resting pack still takes on anyone who comes too close.
- You die → **spectator** (`state='spec'`, free camera WASD/Space/C/Shift) for **90 s**, then back at your fire with full
  health and satiety. Dev (panel open with the backquote key) can press **R** to come back at once. **Esc** (or Start)
  shows "keep watching / leave the war" (not visually checked yet).
- HUD: bottom left your side's figures (you first), bottom right theirs, no backgrounds; a skull replaces anyone down.
  Thin capture bar at top while a fire is being taken.
- Danger music reacts to enemy people as to predators. Friendly fire is on.

#### Online (in WAR)

- `MP = W.mp` (`{host, me, players:[{id,name,side}], bots:{A,B}}`), `ON` true when connected, `HOST` = this machine runs
  the war. The host runs bots, captures, place ends; others follow.
- Each player is simulated on their own machine and appears elsewhere as a **puppet** (`NPCB.spawnAt` with
  `n.remote=true`, moved by `window.__NETPUP`; its band has `remote=true` so the AI skips it).
- Messages (type → meaning):
  - `gp` player state 15/s (pos, heading, crouch, alive, spear in hand). In the pause menu you still count as alive.
  - `gb` host's bots 10/s. `gw` fire owners and capture progress. `ga` a blow begun (played on the puppet; it now ends
    after its duration). `gs` a thrown spear (seen, harmless: `visSpear`). `gh` a blow landed on someone who lives on
    another machine (`__NETHIT` sends; the victim's machine applies it; a hit in the pause menu un-pauses).
    `gc` / `gn` / `go` host's cards, next place, war over. `gr` recall request to the host.
  - **Animals:** `gO` host's ownership map, `gA` animal states 10/s from their owner, `gX` a blow on an animal run
    elsewhere, `gE` a carcass eaten. Each animal is run by the machine of the **nearest player** (host decides twice a
    second, 6 m hysteresis); others ease toward reports. Ground birds are not shared.
- Leaving to the menu leaves the room; if the host leaves, others are sent to the menu. Online, the pause menu does not stop
  the war (`window.__MPPAUSE`).
- Hooks: `__NETHIT`, `__NETACT`, `__NETTHROW`, `__NETPUP`, `__MPPAUSE`, `__SPEC`, `__specPad`.

### Other folders

- `src/levels/*.txt` per-level values; `src/levels/img/flag-*.jpg` flags (Matt's crops, 448×256).
- `src/people/*.glb` the three peoples; `img/*.webp` figure renders; `img/skull.webp` (cut from Matt's HUD mockup).
  `tools/people.py` → `src/pool/21-people.txt` (`window.__HUMANS`), via `tools/slim.py` / `tools/glb.py`
  (finger tracks dropped, half keys, int16 rotations, idle 6 s, JPEG q78 — needed to fit the 16 MB pool).
- `src/pool/03-chunk.txt` `window.__GBM` = lyrebird, turkey, emu models (emu replaced with Matt's `emu2.glb` on 26 Nov);
  desktop high-quality copies in `src/desktop/hq-models.json`.
- `src/books/`, `src/text/` documents and tutorial text (converters in `tools/`).

---

## 7. Recent history (what changed lately, newest first)

- **v94** Steam app id 5633130 in both products' desktop apps.
- **v93** Shared animals online; spectator exit menu.
- **v92** Online folded into main. Puppet blow pose fixed; hits land in the pause menu; bot formation ahead; J recall; bots
  defend against stalking predators.
- **v91** Bots keep fighting while you spectate (they froze).
- **v90** Warfare: all fires lit; maps coloured by owner; war to-do list on the map.
- **v89** HUD figures without cards, skull for the down.
- **v88** Big round: shared — new emu, breathing −20%, fort gangway gap at the gate and lower stakes (standing on the
  walkway you see over, crouched you are covered), pause screen simplified, hollow log/shack/bark hut predator-proof.
  X — the war restarts after a run reset (this was why bots "often didn't spawn"), 90 s spectator respawn with full satiety,
  bots follow, animal-style detection on people, predators take on anyone too near, teams rally, flags clear of collision,
  figure HUD, team select beside the menu, NPC spears 20% smaller.
- Before that (v70–v87): source recovered from the v70 build after an environment reset; people system; warfare offline;
  survival/X split; document placement audit; waterfall in the upper gully; diprotodon stampedes; coats (Blue-tongue
  replaced Komodo; King of the Bush II removed); chimneys cave in when not the main fire; cliffs west side widened.

---

## 8. Open items (as of 27 Nov 2026)

### Waiting on Matt

1. **Steam test on two computers** (never done). Second account needs a developer key. Steps: both open X v94 app →
   warfare → one "host online" (choose people, war length, place) → read code → other "join online" → host sets bots →
   start. Ask where it fails if it does: creating, joining, lobby, loading, seeing each other.
2. **GitHub**: push the bundle to `swsldr93/BONEAGE` (or have you do it). Delete the personal access token he pasted into
   the old chat (it was never used).
3. **Visual checks in gully/cliffs** of the fort gangway gap/stake height and shelter protection (never seen here).
4. **Silent warfare** ("loads without ambient or other sounds"): could not reproduce; output level measured normal.
   Need: browser or app, which place, first place or after moving on.
5. Survival test release decisions: Steam Playtest (recommended), version number on the menu, a feedback channel.

### Known gaps / ideas not built

- Online: late join and reconnect; ground birds not shared; a predator hunts only the player whose machine runs it;
  moving between places together and the end of a war were never fully run across two copies; the room-code high-bits
  assumption unverified.
- No visible version number on the menu yet (Matt agreed it would help testers).
- Piracy measures offered, not built: per-tester marked builds, an expiry date in test builds.
- Trademark for "Bone Age" with IP Australia (advice given; his decision).
- Survival "ready?" verdict given: fine for a small closed test with trusted people after the visual checks, a version
  number and a feedback route; not for public.

---

## 9. Practical cautions

- `src/engine.html` is huge; edit with exact string replacements and check that each replaced string occurs once.
- Many functions are redefined per level inside `//@if` blocks — the same name can appear 2–3 times; edit the right one.
- Wrappers are layered (`hurtPlayer`, `hitAnimal`, `showDeath`, `resetRun`, `updateCamera`, `baReload`, `doThrustHit` …
  are reassigned by NPCB and WAR). A wrapper added later wins; call through the current binding, not a saved property.
- `resetRun` clears all people (NPCB reset); WAR restarts itself after it.
- Keep `pool.js` < 16 MB.
- After the build, `out/web` is recreated: restart any local http server serving it.
- Survival builds: build in the `survival` worktree; its desktop build also needs `tools/cache`, `tools/node/node_modules`
  and a Mac shell zip in its own `out/`.
