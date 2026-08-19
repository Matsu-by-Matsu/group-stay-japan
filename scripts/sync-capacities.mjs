import fs from 'node:fs';
import vm from 'node:vm';

const indexPath = 'index.html';
const catalogPath = '_SYSTEM/catalog.js';
const propertyPath = '_SYSTEM/property.html';
const index = fs.readFileSync(indexPath, 'utf8');
const property = fs.readFileSync(propertyPath, 'utf8');
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(catalogPath, 'utf8'), context);

const baseBlock = index.match(/const stays=\[([\s\S]*?)\];/);
if (!baseBlock) throw new Error('Base stay catalog not found');
const base = vm.runInNewContext(`[${baseBlock[1]}]`);
const extras = context.window.GSJ_EXTRA_STAYS || [];
const details = context.window.GSJ_EXTRA_PROPERTIES || {};
const sourceById = {};
for (const match of property.matchAll(/'([^']+)'\s*:\s*\{[^\n]*?source:'([^']+)'/g)) sourceById[match[1]] = match[2];
for (const [id, item] of Object.entries(details)) sourceById[id] = item.source;

function capacities(html) {
  const values = [];
  const patterns = [
    /c-rooms-spec-detail-term[^>]*>\s*定員\s*<[^>]+>\s*<dd[^>]*>\s*(\d+)\s*人/gi,
    /<dt>\s*定員\s*<\/dt>\s*<dd>\s*(\d+)\s*人/gi,
    /<div class="capacity">[\s\S]{0,180}?<span class="content">\s*(\d+)\s*名/gi,
    /max(?:imum)?\s*(\d+)\s*(?:people|guests)/gi,
    /up to\s*(\d+)\s*guests/gi,
    /accommodates?\s+up to\s*(\d+)/gi,
    /最大\s*(\d+)\s*名/gi,
    /定員[^<]{0,40}<[^>]+>\s*(\d+)\s*名/gi
  ];
  for (const pattern of patterns) for (const match of html.matchAll(pattern)) values.push(Number(match[1]));
  return [...new Set(values.filter((n) => n >= 2 && n <= 20))].sort((a, b) => a - b);
}

const all = [...base, ...extras];
const results = {};
for (const [position, stay] of all.entries()) {
  const source = sourceById[stay.id];
  if (!source) {
    results[stay.id] = { source: null, values: [], error: 'missing source' };
    continue;
  }
  try {
    const response = await fetch(source, { headers: { 'user-agent': 'Mozilla/5.0 GROUP-STAY-JAPAN capacity verifier' }, signal: AbortSignal.timeout(30000) });
    const html = await response.text();
    const values = capacities(html);
    results[stay.id] = { source, values, min: values[0] ?? null, max: values.at(-1) ?? null, status: response.status };
  } catch (error) {
    results[stay.id] = { source, values: [], min: null, max: null, error: error.message };
  }
  console.log(`${position + 1}/${all.length} ${stay.id}: ${results[stay.id].values.join('-') || 'UNVERIFIED'}`);
}

let nextIndex = index;
for (const stay of base) {
  const result = results[stay.id];
  const max = result?.max;
  if (!max) continue;
  const linePattern = new RegExp(`(\\{id:'${stay.id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}'[^\\n]*?max:)(?:null|\\d+)`);
  nextIndex = nextIndex.replace(linePattern, `$1${max}`);
}

for (const stay of extras) {
  const result = results[stay.id];
  stay.min = result?.min ?? null;
  stay.max = result?.max ?? null;
  if (details[stay.id]) {
    details[stay.id].min = stay.min;
    details[stay.id].max = stay.max;
    details[stay.id].capacityVerified = Boolean(stay.max);
    details[stay.id].capacitySource = result?.source ?? null;
  }
}

const catalog = `window.GSJ_EXTRA_STAYS=${JSON.stringify(extras)};\nwindow.GSJ_EXTRA_PROPERTIES=${JSON.stringify(details)};\n`;
fs.writeFileSync(indexPath, nextIndex, 'utf8');
fs.writeFileSync(catalogPath, catalog, 'utf8');
fs.writeFileSync('scripts/capacity-audit.json', `${JSON.stringify(results, null, 2)}\n`, 'utf8');

const verified = Object.values(results).filter((item) => item.max).length;
console.log(`Verified ${verified}/${all.length} properties.`);
if (verified !== all.length) process.exitCode = 2;
