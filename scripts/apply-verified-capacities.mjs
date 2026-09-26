import fs from 'node:fs';import vm from 'node:vm';
const rooms=JSON.parse(fs.readFileSync('data/room-model.json','utf8').replace(/^\uFEFF/,''));const by=Object.fromEntries(rooms.map(p=>[p.id,p]));const ctx={window:{}};vm.runInNewContext(fs.readFileSync('_SYSTEM/catalog.js','utf8'),ctx);
for(const p of ctx.window.GSJ_EXTRA_STAYS||[]){if(by[p.id]&&!by[p.id].excluded)p.max=by[p.id].max;}
for(const [id,p] of Object.entries(ctx.window.GSJ_EXTRA_PROPERTIES||{})){if(by[id]&&!by[id].excluded)p.max=by[id].max;}
fs.writeFileSync('_SYSTEM/catalog.js',`window.GSJ_EXTRA_STAYS=${JSON.stringify(ctx.window.GSJ_EXTRA_STAYS)};\nwindow.GSJ_EXTRA_PROPERTIES=${JSON.stringify(ctx.window.GSJ_EXTRA_PROPERTIES)};\n`);
for(const file of ['index.html','_SYSTEM/property.html']){let h=fs.readFileSync(file,'utf8');for(const p of rooms){if(p.excluded)continue;const id=p.id;const re=file==='index.html'?new RegExp(`(\\{id:'${id}'[^\\n]*?max:)(?:null|\\d+)`):new RegExp(`('${id}'\\s*:\\s*\\{[^\\n]*?max:)(?:null|\\d+)`);h=h.replace(re,(_,prefix)=>prefix+p.max);}fs.writeFileSync(file,h);}
console.log('Synchronized official capacities in existing catalogs.');
