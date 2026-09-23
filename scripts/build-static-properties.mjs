import { propertyRoomGuide } from './verified-room-comparisons.mjs';
import { japaneseRoomSize } from './property-language.mjs';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const template=fs.readFileSync(path.join(root,'_SYSTEM/property.html'),'utf8');
const ctx={window:{}};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(root,'_SYSTEM/catalog.js'),'utf8'),ctx);
const start=template.indexOf('const properties='),end=template.indexOf('const copy=',start);
if(start<0||end<0)throw Error('Template data boundaries missing');
vm.runInContext(template.slice(start,end)+';globalThis.data=properties;',ctx);
vm.runInContext(template.slice(end,template.indexOf('const localized=',end))+';globalThis.translations=copy;',ctx);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const json=v=>JSON.stringify(v).replace(/</g,'\\u003c');
const route=(id,lang)=>`${lang==='ja'?'/ja':''}/stays/${encodeURIComponent(id)}/`;
const origin='https://groupstayjapan.synthx.jp';
const ids=Object.keys(ctx.data);
const legacy=`(()=>{if(location.pathname!=='/_SYSTEM/property.html')return;const q=new URLSearchParams(location.search),id=q.get('id');if(!${json(ids)}.includes(id))return;const lang=q.get('lang')==='ja'?'ja':'en';const target=new URL((lang==='ja'?'/ja':'')+'/stays/'+encodeURIComponent(id)+'/',location.origin);q.delete('id');q.delete('v');target.search=q.toString();target.hash=location.hash;const canonical=document.createElement('link');canonical.rel='canonical';canonical.href=target.origin+target.pathname;document.head.appendChild(canonical);location.replace(target.href);})();`;
fs.writeFileSync(path.join(root,'assets/legacy-property-redirect.js'),legacy+'\n');
for(const [id,original] of Object.entries(ctx.data))for(const lang of ['en','ja']){
 if(!/^[a-z0-9-]+$/.test(id))throw Error('Invalid ID');
 const ja=lang==='ja',p={...original,photos:original.photos.map(u=>u.replace(/^\.\.\//,'/'))},t=ctx.translations[lang];
 if(ja)p.size=japaneseRoomSize(p.size);
 const jp={name:p.name,place:p.place,address:p.address,description:`${p.name}（${p.place}）の宿泊情報です。${p.max?`掲載情報の最大宿泊人数は${p.max}名です。`:''}${p.size&&p.size!=='客室タイプによる'?`客室面積：${japaneseRoomSize(original.size)}。`:''}定員・寝具・設備は客室タイプによって異なります。住所と施設情報を確認し、宿泊日と人数に合う部屋を予約先で選んでください。`,area:`${p.name}の所在地は${p.address}です。交通手段やチェックイン方法の詳細は施設情報の出典と予約先で確認してください。`,beds:[['寝具構成','選択した客室の条件をご確認ください']],bedCount:'客室タイプによる'};
 const x=ja?jp:{...p,description:`${p.name} is in ${p.place}. ${p.description}`};
 const canonical=origin+route(id,lang);
 let h=template.slice(0,start)+`const properties=${json({[id]:p})};\n`+template.slice(end);
 h=h.replace('<script src="catalog.js"></script>','').replace('<script src="/assets/legacy-property-redirect.js"></script>','')
 .replace(/document\.title=[^;]+;/g,'')
 .replaceAll('../index.html','/').replace('<html lang="en">',`<html lang="${lang}">`)
 .replace("properties[params.get('id')]?params.get('id'):'minn-okuasakusa'",json(id))
 .replace(/let language=[\s\S]*?;const propertyId=/,`let language=['zh-TW','ko'].includes(params.get('lang'))?params.get('lang'):${json(lang)};const propertyId=`)
 .replace('function nights(){',`localized[${json(id)}].ja=${json(jp)};function nights(){`)
 .replace(/<title>[^<]*<\/title>/,`<title>${esc(p.name)} · ${esc(p.place)}${ja?'の宿泊・客室情報':''} | GROUP STAY JAPAN</title>`)
 .replace(/<meta name="description" content="[^"]*">/,`<meta name="description" content="${esc(ja?jp.description:`${p.name} in ${p.place}. Address, room information, photos and booking options. Confirm the selected room's capacity and beds before booking.`)}">`);
 const head=`<link rel="canonical" href="${canonical}"><link rel="alternate" hreflang="en" href="${origin+route(id,'en')}"><link rel="alternate" hreflang="ja" href="${origin+route(id,'ja')}"><link rel="alternate" hreflang="x-default" href="${origin+route(id,'en')}"><script type="application/ld+json">${json({'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:[{'@type':'ListItem',position:1,name:ja?'宿一覧':'Stays',item:origin+'/'},{'@type':'ListItem',position:2,name:p.name,item:canonical}]})}</script>`;
 // Explicit language parameters can resolve to their static locale; never redirect from browser settings.
 const routing=`(()=>{const q=new URLSearchParams(location.search),lang=q.get('lang');if((lang==='ja'||lang==='en')&&lang!==${json(lang)}){const u=new URL((lang==='ja'?'/ja':'')+'/stays/'+${json(id)}+'/',location.origin);u.search=q.toString();u.hash=location.hash;location.replace(u.href)}})();`;
 h=h.replace('</head>',head+'</head>').replace('<head>','<head><script>'+routing+'</script>');
 const fields={operator:p.operator,name:p.name,location:p.place,max:p.max||(ja?'客室タイプによる':'Varies by room'),size:ja&&p.size==='Room-dependent'?'客室タイプによる':p.size,bedCount:x.bedCount||'Varies by room',description:x.description,areaCopy:x.area,address:p.address,mapAddress:p.address,checkinRule:p.checkin,checkoutRule:p.checkout,cleaning:t.clean};
 for(const [key,val] of Object.entries(fields)){
 const re=new RegExp(`(<[a-z0-9]+[^>]*\\bid="${key}"[^>]*>)[^<]*(</[a-z0-9]+>)`);
 if(!re.test(h))throw Error(`Missing ${id}/${key}`);h=h.replace(re,(_,a,b)=>a+esc(val)+b);
 }
 h=h.replace(/(<([a-z0-9]+)[^>]*data-t="([^"]+)"[^>]*>)[^<]*(<\/\2>)/g,(_,a,tag,key,b)=>a+esc(t[key]||ctx.translations.en[key]||key)+b);
 h=h.replace('<div class="beds" id="bedLayout"></div>',`<div class="beds" id="bedLayout">${x.beds.map(([n,c])=>`<div class="bed"><b>${esc(n)}</b><br>× ${esc(c)}</div>`).join('')}</div>`);
 h=h.replace('<div class="gallery" id="gallery"></div>',`<div class="gallery" id="gallery">${p.photos.slice(0,5).map((u,i)=>`<button type="button" aria-label="Open photo ${i+1}"><img src="${esc(u)}" alt="${esc(p.name)} ${ja?'施設写真':'photo'} ${i+1}" loading="${i?'lazy':'eager'}"></button>`).join('')}</div>`);
 h=h.replace('</main>',`<section class="wrap section"><h2>${ja?'予約前に客室の条件をご確認ください':'Check the exact room before booking'}</h2><p>${ja?'定員・寝具・設備・キャンセル条件は、選択した部屋と宿泊日によって異なります。施設の最大定員で、すべての部屋に泊まれるわけではありません。':'Capacity, beds, facilities and cancellation terms depend on the selected room and dates. A property’s maximum capacity does not apply to every room.'}</p><p><a style="text-decoration:underline" href="${esc(p.source)}" target="_blank" rel="noopener">${esc(p.name)} — ${ja?'施設情報の出典':'source information'}</a></p><p><a id="partnerLink" style="text-decoration:underline" href="${esc(p.partner||p.source)}" target="_blank" rel="sponsored noopener">${ja?'Trip.comで空室・料金を確認':'Check availability and prices on Trip.com'}</a></p><p class="small">${ja?'予約リンクはアフィリエイトリンクです。予約が成立すると当サイトに報酬が支払われる場合があります。':'These are affiliate booking links. We may receive a commission when you book.'}</p><nav aria-label="Language"><a href="${route(id,'en')}">English</a> · <a href="${route(id,'ja')}">日本語</a></nav></section></main>`);
 h=h.replace('<section class="section" id="mapSection">',propertyRoomGuide(id,lang,esc)+'<section class="section" id="mapSection">');
 const extra=`document.getElementById('lang').addEventListener('change',e=>{const next=e.target.value;if(next==='en'||next==='ja'){const u=new URL((next==='ja'?'/ja':'')+'/stays/'+propertyId+'/',location.origin);const q=new URLSearchParams(location.search);q.set('lang',next);q.set('checkIn',checkIn.value);q.set('checkOut',checkOut.value);q.set('guests',guests.value);u.search=q.toString();location.assign(u.href)}});document.getElementById('partnerLink').addEventListener('click',e=>{e.preventDefault();booking.requestSubmit()});`;
 h=h.replace('</body>',`<script>${extra}</script></body>`);
 const dir=path.join(root,route(id,lang));fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,'index.html'),h);
}
console.log(`Built ${ids.length*2} English/Japanese static property pages and legacy redirect`);
