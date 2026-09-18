import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=process.cwd(), sitemap=fs.readFileSync('sitemap.xml','utf8'), ids=fs.readdirSync('stays');
const template=fs.readFileSync('_SYSTEM/property.html','utf8');
const booking=h=>h.slice(h.indexOf('booking.onsubmit=')).split('</script>')[0];
assert.equal(ids.length,81);
const titles=new Set();
for(const id of ids){
 const h=fs.readFileSync(`stays/${id}/index.html`,'utf8');
 const body=h.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g,'');
 const canonical=`https://groupstayjapan.synthx.jp/stays/${id}/`;
 assert.equal((h.match(/<link rel="canonical"/g)||[]).length,1,id);
 assert.ok(h.includes(`href="${canonical}"`),id);
 assert.ok(sitemap.includes(`<loc>${canonical}</loc>`),id);
 assert.ok(h.includes(`const propertyId=${JSON.stringify(id)},`),id);
 for(const field of ['name','description','address','location'])assert.match(body,new RegExp(`id="${field}">[^<]+<`),`${id}/${field}`);
 assert.ok(!h.includes('../assets/'),id);
 assert.ok(!h.includes('../index.html'),id);
 assert.equal(booking(h),booking(template),`${id}: booking behavior`);
 titles.add(h.match(/<title>(.*?)<\/title>/)[1]);
 for(const m of h.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g))if(m[2].trim())new vm.Script(m[2]);
 for(const m of body.matchAll(/(?:src|href)="(\/[^"?#]*)(?:[^" ]*)"/g)) assert.ok(fs.existsSync(path.join(root,m[1])),`${id}: missing ${m[1]}`);
}
assert.equal(titles.size,ids.length);
assert.ok(!sitemap.includes('property.html?id='));
console.log(`PASS: ${ids.length} static pages: unique titles, bodies, canonicals, sitemap, local assets, booking handlers and JavaScript syntax.`);
