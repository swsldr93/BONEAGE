// parse every inline script of each level page; report syntax errors (pool placeholders filled from pool.js)
const fs=require('fs'), vm=require('vm'); const D=process.argv[2];
global.window=global; eval(fs.readFileSync(D+'/pool.js','utf8'));
for(const lv of ['plains','gully','escarpment']){ global.BA_PGLV={}; global.BA_PGGEN={}; eval(fs.readFileSync(D+'/pg-'+lv+'.js','utf8'));
  let s=BA_PGLV[lv]; s=s.replace(/@@P(\d+)@@/g,(m,i)=>BA_POOL[+i]);
  const re=/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g; let m, n=0, bad=0;
  while((m=re.exec(s))){ n++; const code=m[1]; try{ new vm.Script(code.includes('/*@@GEN0@@*/')?'(function*(){'+code+'})':code); }catch(e){ bad++; console.log(lv,'script',n,e.message, JSON.stringify(code.slice(0,60))); } }
  console.log(lv,'scripts',n,'errors',bad); }
