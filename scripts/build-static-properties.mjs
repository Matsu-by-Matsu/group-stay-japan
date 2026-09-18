import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const template = fs.readFileSync(path.join(root, '_SYSTEM/property.html'), 'utf8');
const context = {window: {}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, '_SYSTEM/catalog.js'), 'utf8'), context);
const start = template.indexOf('const properties=');
const end = template.indexOf('const copy=', start);
if (start < 0 || end < 0) throw new Error('Property data boundaries missing');
vm.runInContext(template.slice(start, end) + ';globalThis.data=properties;', context);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const json = value => JSON.stringify(value).replace(/</g, '\\u003c');
const route = id => `/stays/${encodeURIComponent(id)}/`;
for (const [id, original] of Object.entries(context.data)) {
  if (!/^[a-z0-9-]+$/.test(id)) throw new Error(`Invalid property ID: ${id}`);
  const p = {...original, photos: original.photos.map(url => url.replace(/^\.\.\//, '/'))};
  const canonical = `https://groupstayjapan.synthx.jp${route(id)}`;
  let html = template.slice(0, start) + `const properties=${json({[id]: p})};\n` + template.slice(end);
  html = html.replace('<script src="catalog.js"></script>', '')
    .replaceAll('../index.html', '/index.html')
    .replace("properties[params.get('id')]?params.get('id'):'minn-okuasakusa'", json(id))
    .replace(/<title>[^<]*<\/title>/, `<title>${esc(p.name)} · ${esc(p.place)} | GROUP STAY JAPAN</title>`)
    .replace(/<meta name="description" content="[^"]*">/, `<meta name="description" content="${esc(`${p.name} in ${p.place}. Address, room information, photos and booking options. Confirm the selected room's capacity and beds before booking.`)}">`)
    .replace('</head>', `<link rel="canonical" href="${canonical}"></head>`);
  const fields = {operator:p.operator,name:p.name,location:p.place,max:p.max || 'Varies by room',size:p.size,bedCount:p.bedCount || 'Varies by room',description:`${p.name} is in ${p.place}. ${p.description}`,areaCopy:p.area,address:p.address,mapAddress:p.address,checkinRule:p.checkin,checkoutRule:p.checkout};
  for (const [key, value] of Object.entries(fields)) {
    const re = new RegExp(`(<[a-z0-9]+[^>]*\\bid="${key}"[^>]*>)[^<]*(</[a-z0-9]+>)`);
    if (!re.test(html)) throw new Error(`Missing field ${id}/${key}`);
    html = html.replace(re, (_, a, b) => a + esc(value) + b);
  }
  html = html.replace('<div class="beds" id="bedLayout"></div>', `<div class="beds" id="bedLayout">${p.beds.map(([name,count])=>`<div class="bed"><b>${esc(name)}</b><br>× ${esc(count)}</div>`).join('')}</div>`);
  html = html.replace('<div class="gallery" id="gallery"></div>', `<div class="gallery" id="gallery">${p.photos.slice(0,5).map((url,i)=>`<button type="button" aria-label="Open photo ${i+1}"><img src="${esc(url)}" alt="${esc(p.name)} photo ${i+1}" loading="${i?'lazy':'eager'}"></button>`).join('')}</div>`);
  html = html.replace('</main>', `<section class="wrap section"><h2>Check the exact room before booking</h2><p>Capacity, beds, facilities and cancellation terms depend on the selected room and dates. A property's maximum capacity does not apply to every room.</p><p><a style="text-decoration:underline" href="${esc(p.source)}" target="_blank" rel="noopener">${esc(p.name)} — source information</a></p><noscript><p><a href="${esc(p.partner || p.source)}" rel="sponsored noopener">Check availability and room conditions</a></p></noscript></section></main>`);
  const dir = path.join(root, 'stays', id);
  fs.mkdirSync(dir, {recursive:true});
  fs.writeFileSync(path.join(dir, 'index.html'), html);
}
console.log(`Built ${Object.keys(context.data).length} static property pages`);
