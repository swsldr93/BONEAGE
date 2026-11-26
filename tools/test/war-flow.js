// node poi.js <level> <kinds,comma> <prefix> : start the level with those POIs forced, photograph each from two sides
// node tools/test/war-flow.js "<place name>"  (serve out/web on port 8765 first): starts a quick war there and reports state, bots, audio
const {chromium}=require('playwright'); const fs=require('fs');
const OUT=require('path').resolve(__dirname,'../../out/web')+'/', S=__dirname+'/shots/';
const [lv,kinds,pre,fk]=process.argv.slice(2);
(async()=>{ const b=await chromium.launch({args:['--disable-dev-shm-usage','--js-flags=--max-old-space-size=6000','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:480,height:270}});
 await p.route(/cdnjs.cloudflare.com.*three.min.js/,r=>r.fulfill({path:require('path').resolve(__dirname,'../../src/desktop/app/three.min.js'),contentType:'text/javascript',headers:{'access-control-allow-origin':'*'}}));
 await p.route(/fonts.(googleapis|gstatic).com/,r=>r.fulfill({body:'',contentType:'text/css'}));
 await p.route(/pg-\w+\.js/,async r=>{ const f=OUT+r.request().url().split('/').pop().split('?')[0]; const raw=fs.readFileSync(f,'utf8'); const l=f.match(/pg-(\w+)\.js/)[1];
   global.BA_PGLV={}; global.BA_PGGEN={}; global.window=global; eval(raw); let s=BA_PGLV[l], G=BA_PGGEN[l];
   const g0=s.indexOf('/*@@GEN0@@*/')+12, at=s.indexOf('const BODY_VIS=[];')+'const BODY_VIS=[];'.length, add=' window.__T=(s)=>eval(s);';
   s=s.slice(0,at)+add+s.slice(at); G.ins.forEach(x=>{ if(x[0]>=at-g0) x[0]+=add.length; });
   r.fulfill({body:'window.BA_PGLV=window.BA_PGLV||{}; BA_PGLV.'+l+'='+JSON.stringify(s).replace(/<\//g,'<\\/')+'; window.BA_PGGEN=window.BA_PGGEN||{}; BA_PGGEN.'+l+'='+JSON.stringify(G)+';',contentType:'text/javascript'}); });
 const errs=[]; p.on('pageerror',e=>{ const m=String(e); if(!/map only/.test(m)) errs.push(m.slice(0,300)); });
 const log=(...a)=>console.log(new Date().toISOString().slice(11,19),...a);
 await p.addInitScript(()=>{ window.__errs=[]; window.addEventListener('error',e=>{ if(window.__errs.length<8) window.__errs.push(String(e.message)+' @'+(e.lineno||'')+':'+(e.colno||'')); }); }); await p.goto('http://localhost:8765/index.html'); await p.waitForTimeout(2500);
 await p.evaluate(()=>{ try{ const o=BA_PLAT.get('settings')||{}; Object.assign(o,{quality:'low',shad:0,fx:0}); BA_PLAT.set('settings',o); }catch(e){} });
 await p.mouse.click(240,135); await p.waitForTimeout(500); await p.keyboard.press('Space'); await p.waitForTimeout(800); await p.keyboard.press('Space'); await p.waitForTimeout(2500);
 await p.evaluate(()=>document.getElementById('warL').click()); await p.waitForTimeout(500);
 await p.evaluate(()=>document.querySelector('#warCols [data-people]').click()); await p.waitForTimeout(400);
 await p.evaluate(()=>document.querySelector('#warList button').click()); await p.waitForTimeout(400);
 const PL=process.argv[2]||'high plains'; log('places',await p.evaluate(()=>[...document.querySelectorAll('#warList button')].map(b=>b.textContent).join('|')));
 await p.evaluate(pl=>{ const b=[...document.querySelectorAll('#warList button')].find(b=>b.textContent.includes(pl)); b.click(); },PL);
 const fw=async(code)=>{ for(const f of p.frames()){ if(f===p.mainFrame()) continue; try{ const r=await f.evaluate(c=>{ if(typeof window.__T!=='function') return null; try{ return JSON.stringify(window.__T(c)); }catch(e){ return 'ERR '+e.message; } },code); if(r!=null) return r; }catch(e){} } return 'NOFRAME'; };
 const gp=setInterval(async()=>{ for(const f of p.frames()){ if(f===p.mainFrame()) continue; try{ await f.evaluate(()=>{ if(window.__BA_DBG&&!window.__rr&&window.__T){ const r=window.__T('renderer'); if(r){ window.__rr=r.render.bind(r); r.render=()=>{}; } } }); }catch(e){} } },300); let np=0; for(let i=0;i<50;i++){ await p.waitForTimeout(3000); const s=await fw("state+'|'+(window.__WAR?('war bots='+__WAR.bots.length):'nowar')+'|live='+NPCB.list.filter(n=>n.alive).length+'|lvg='+(A&&A.master?A.master.gain.value.toFixed(2):'-')+'|ctx='+(A.ctx?A.ctx.state:'-')+'|E='+JSON.stringify(window.__errs)"); log(s); if(/^"tut/.test(s)){ try{ await p.mouse.click(240,135); }catch(e){} await p.keyboard.press('KeyT'); await p.waitForTimeout(400); await p.keyboard.press('Space'); } if(/^"play/.test(s)&&(++np)>4) break; }
 log('top',await p.evaluate(()=>JSON.stringify({ab:window.__BA_AMBBUS&&window.__BA_AMBBUS.gain.value, lvgs:(window.__BA_LVGS||[]).map(o=>[o.lv.gain.value.toFixed(2),o.amb.gain.value.toFixed(2)])})));
 log('errors',JSON.stringify(errs.slice(0,6))); await b.close(); })();
