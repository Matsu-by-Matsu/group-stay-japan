import { execFileSync } from 'node:child_process';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
export const KEY = 'a81c51a96468e9ebf43b53453bfa882c';
const ORIGIN = 'https://groupstayjapan.synthx.jp';
const KEY_URL = `${ORIGIN}/${KEY}.txt`;
const git = (...args) => execFileSync('git', args, { cwd: ROOT });
const decodeXml = s => s.replace(/&(?:amp|lt|gt|quot|apos);/g, x => ({ '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'" })[x]);

export function fileUrl(file) {
  if (file === 'index.html') return `${ORIGIN}/`;
  if (file.endsWith('/index.html')) return `${ORIGIN}/${file.slice(0, -10)}`;
  if (/^_SYSTEM\/[^/]+\.html$/.test(file)) return `${ORIGIN}/${file}`;
  return null;
}

export function collect(args) {
  const all = args.includes('--all');
  const dryRun = args.includes('--dry-run');
  const refs = args.filter(a => !a.startsWith('--'));
  if (args.some(a => a.startsWith('--') && !['--all', '--dry-run'].includes(a)) ||
      (all ? refs.length !== 0 : refs.length !== 2)) {
    throw new Error('Usage: node scripts/indexnow-submit.mjs [--all | <before> <after>] [--dry-run]');
  }
  const sitemap = new Set();
  for (const name of readdirSync(ROOT).filter(n => n === 'sitemap-core.xml' || /^sitemap-stays-.*\.xml$/.test(n)).sort()) {
    for (const match of readFileSync(resolve(ROOT, name), 'utf8').matchAll(/<loc>\s*([^<]+?)\s*<\/loc>/g)) {
      const url = decodeXml(match[1]);
      if (new URL(url).origin !== ORIGIN) throw new Error(`Unexpected sitemap host: ${url}`);
      sitemap.add(url);
    }
  }
  if (!sitemap.size) throw new Error('No sitemap URLs found');
  if (all) return { all, dryRun, urls: [...sitemap], sample: null };
  const commits = refs.map(ref => git('rev-parse', '--verify', '--end-of-options', `${ref}^{commit}`).toString().trim());
  const files = git('diff', '--no-renames', '--diff-filter=AMT', '--name-only', '-z', ...commits, '--', '*.html').toString().split('\0').filter(Boolean);
  const selected = files.map(file => ({ file, url: fileUrl(file) })).filter(x => sitemap.has(x.url));
  return { all, dryRun, urls: [...new Set(selected.map(x => x.url))],
    sample: selected.length ? { url: selected[0].url, body: git('show', `${commits[1]}:${selected[0].file}`) } : null };
}

export async function waitForPublished(url, expected, io) {
  const deadline = io.now() + 600_000;
  while (true) {
    try {
      const response = await io.fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(Math.max(1, Math.min(20_000, deadline - io.now()))) });
      if (response.status === 200 && Buffer.from(await response.arrayBuffer()).equals(expected)) return;
      io.log(`Waiting for published content: ${url} (HTTP ${response.status})`);
    } catch (error) { io.log(`Waiting for published content: ${url} (${error.message})`); }
    const remaining = deadline - io.now();
    if (remaining <= 0) throw new Error(`Publication not confirmed within 10 minutes: ${url}`);
    await io.sleep(Math.min(30_000, remaining));
  }
}

export async function submit(urls, io) {
  let total = 0;
  for (let offset = 0; offset < urls.length; offset += 10_000) {
    const batch = urls.slice(offset, offset + 10_000);
    for (let attempt = 0; attempt < 2; attempt++) {
      const response = await io.fetch('https://api.indexnow.org/indexnow', {
        method: 'POST', headers: { 'Content-Type': 'application/json; charset=utf-8' },
        body: JSON.stringify({ host: 'groupstayjapan.synthx.jp', key: KEY, keyLocation: KEY_URL, urlList: batch }),
        signal: AbortSignal.timeout(30_000),
      });
      const body = await response.text();
      io.log(`IndexNow HTTP ${response.status}; URLs: ${batch.length}`);
      if ([200, 202].includes(response.status)) { total += batch.length; break; }
      io.log(body);
      if (response.status === 429 && attempt === 0) { await io.sleep(600_000); continue; }
      throw new Error(`IndexNow failed: HTTP ${response.status}`);
    }
  }
  io.log(`Submitted URLs: ${total}`);
}

export async function main(args = process.argv.slice(2), overrides = {}) {
  const io = { fetch: globalThis.fetch, sleep, now: Date.now, log: console.log, ...overrides };
  const plan = collect(args);
  io.log(`URL count: ${plan.urls.length}`);
  for (const url of plan.urls) io.log(url);
  if (plan.dryRun || !plan.urls.length) return plan;
  if (!readFileSync(resolve(ROOT, `${KEY}.txt`)).equals(Buffer.from(KEY))) throw new Error('Invalid local key file');
  await waitForPublished(KEY_URL, Buffer.from(KEY), io);
  if (!plan.all) await waitForPublished(plan.sample.url, plan.sample.body, io);
  await submit(plan.urls, io);
  return plan;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
