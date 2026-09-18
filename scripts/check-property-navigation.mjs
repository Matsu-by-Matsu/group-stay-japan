import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
let n=0;
for(const current of ['en','ja'])for(const next of ['en','ja']){
 const h=fs.readFileSync(`${current==='ja'?'ja/':''}stays/minn-akihabara/index.html`,'utf8');const scripts=[...h.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
 let replaced;const location={search:`?lang=${next}&guests=6&checkIn=2026-10-01&checkOut=2026-10-03`,origin:'https://groupstayjapan.synthx.jp',hash:'#map',replace:u=>replaced=u};
 vm.runInNewContext(scripts[0][2],{URL,URLSearchParams,location});
 assert.equal(Boolean(replaced),next!==current);if(replaced){const u=new URL(replaced);assert.equal(u.pathname,`${next==='ja'?'/ja':''}/stays/minn-akihabara/`);assert.equal(u.searchParams.get('guests'),'6')}
 const handlers={};let assigned,submitted=0;
 const elements={lang:{addEventListener:(ev,fn)=>handlers.lang=fn},partnerLink:{addEventListener:(ev,fn)=>handlers.partner=fn}};
 const ctx={URL,URLSearchParams,document:{getElementById:id=>elements[id]},location:{...location,assign:u=>assigned=u},propertyId:'minn-akihabara',checkIn:{value:'2026-11-01'},checkOut:{value:'2026-11-04'},guests:{value:'5'},booking:{requestSubmit:()=>submitted++}};
 vm.runInNewContext(scripts.at(-1)[2],ctx);handlers.lang({target:{value:next}});const u=new URL(assigned);assert.equal(u.pathname,`${next==='ja'?'/ja':''}/stays/minn-akihabara/`);assert.equal(u.searchParams.get('checkIn'),'2026-11-01');assert.equal(u.searchParams.get('checkOut'),'2026-11-04');assert.equal(u.searchParams.get('guests'),'5');handlers.partner({preventDefault(){}});assert.equal(submitted,1);n++;
}
console.log(`PASS: ${n} locale switches/query redirects, selected dates/guests preserved; sponsored link uses validated booking submission.`);
