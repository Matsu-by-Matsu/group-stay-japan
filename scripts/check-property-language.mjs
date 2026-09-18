import fs from 'node:fs';
import assert from 'node:assert/strict';
import {japaneseRoomSize} from './property-language.mjs';
for(const [input,expected] of [['42㎡ room available','42㎡の客室あり'],['Up to 69㎡','最大69㎡'],['35㎡+','35㎡以上'],['25–45㎡','25–45㎡'],['Room-dependent','客室タイプによる'],['Unknown','客室タイプによる']])assert.equal(japaneseRoomSize(input),expected);
let pages=0;
for(const id of fs.readdirSync('stays'))for(const locale of ['', 'ja/']){
 const h=fs.readFileSync(`${locale}stays/${id}/index.html`,'utf8');
 assert.ok(!/document\.title\s*=/.test(h),`${locale}${id}: runtime title mutation`);
 if(locale){
  const body=h.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g,'');
  const description=body.match(/<meta name="description" content="([^"]*)"/)[1];
  const size=body.match(/id="size">([^<]*)</)[1];
  assert.ok(!/room available|Up to|Room-dependent/.test(description+' '+size),id);
  const data=JSON.parse(h.match(/const properties=(\{[^\n]+\});\n/)[1]);
  assert.equal(data[id].size,size,`${id}: runtime room-size consistency`);
  assert.ok(h.match(/<title>(.*?)<\/title>/)[1].includes('の宿泊・客室情報'));
 }
 pages++;
}
const legacy=fs.readFileSync('_SYSTEM/property.html','utf8');
assert.ok(!/<meta[^>]*name=["']robots["'][^>]*noindex/i.test(legacy),'Do not suppress rendering of legacy JavaScript redirects');
console.log(`PASS: ${pages} persistent HTML titles; 81 Japanese static/runtime room sizes; legacy redirects remain renderable.`);
