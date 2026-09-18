import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=process.cwd(),sitemap=fs.readFileSync('sitemap.xml','utf8'),ids=fs.readdirSync('stays');
const template=fs.readFileSync('_SYSTEM/property.html','utf8'),legacy=fs.readFileSync('assets/legacy-property-redirect.js','utf8');
const booking=h=>h.slice(h.indexOf('booking.onsubmit=')).split('</script>')[0];
const titles=new Set();let count=0;
assert.equal(ids.length,81);
for(const id of ids)for(const lang of ['en','ja']){
 const route=(lang==='ja'?'/ja':'')+`/stays/${id}/`, h=fs.readFileSync('.'+route+'index.html','utf8');
 const body=h.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g,'');
 const canonical='https://groupstayjapan.synthx.jp'+route;
 assert.equal((h.match(/<link rel="canonical"/g)||[]).length,1,id);
 assert.ok(h.includes(`href="${canonical}"`),id);assert.ok(sitemap.includes(`<loc>${canonical}</loc>`),id);
 assert.ok(h.includes(`const propertyId=${JSON.stringify(id)},`),id);
 assert.ok(h.includes(`<html lang="${lang}">`));
 for(const field of ['name','description','address','location'])assert.match(body,new RegExp(`id="${field}">[^<]+<`),`${id}/${field}`);
 if(lang==='ja'){assert.ok(body.includes('予約前に客室の条件をご確認ください'));assert.ok(body.includes('の宿泊情報です。'));assert.ok(!body.includes('About this stay'));}
 for(const l of ['en','ja'])assert.ok(h.includes(`hreflang="${l}" href="https://groupstayjapan.synthx.jp${l==='ja'?'/ja':''}/stays/${id}/"`));
 assert.ok(!h.includes('../assets/'));assert.ok(!h.includes('index.html'));assert.ok(!h.includes('legacy-property-redirect.js'));
 assert.equal(booking(h),booking(template),`${id}: booking behavior`);
 assert.match(body,/<a id="partnerLink"[^>]*rel="sponsored noopener"/);
 titles.add(h.match(/<title>(.*?)<\/title>/)[1]);
 for(const m of h.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)){
  if(m[1].includes('application/ld+json'))assert.equal(JSON.parse(m[2])['@type'],'BreadcrumbList');
  else if(m[2].trim())new vm.Script(m[2]);
 }
 for(const m of body.matchAll(/(?:src|href)="(\/[^"?#]*)(?:[^" ]*)"/g))assert.ok(fs.existsSync(path.join(root,m[1])),`${id}: missing ${m[1]}`);
 count++;
}
assert.equal(titles.size,162);assert.equal((sitemap.match(/<loc>/g)||[]).length,181);assert.ok(!sitemap.includes('property.html?id='));
let redirects=0;
for(const id of [...ids,'bad-id'])for(const lang of ['en','ja','ko','zh-TW']){
 let target,canonical;
 const location={pathname:'/_SYSTEM/property.html',search:`?id=${id}&lang=${lang}&guests=6&checkIn=2026-10-01&checkOut=2026-10-03&v=old`,origin:'https://groupstayjapan.synthx.jp',hash:'#rooms',replace:u=>target=u};
 vm.runInNewContext(legacy,{URL,URLSearchParams,location,document:{createElement:()=>({}),head:{appendChild:e=>canonical=e.href}}});
 if(id==='bad-id'){assert.equal(target,undefined);continue;}
 const u=new URL(target);assert.equal(u.pathname,`${lang==='ja'?'/ja':''}/stays/${id}/`);assert.equal(canonical,u.origin+u.pathname);
 for(const [k,v] of Object.entries({lang,guests:'6',checkIn:'2026-10-01',checkOut:'2026-10-03'}))assert.equal(u.searchParams.get(k),v);
 assert.equal(u.searchParams.has('id'),false);assert.equal(u.hash,'#rooms');redirects++;
}
console.log(`PASS: ${count} localized static pages, reciprocal hreflang, schema, sponsored links, assets, canonicals and booking handlers; ${redirects} legacy redirects plus invalid IDs.`);
