/* GROUP STAY JAPAN top page (v15). Switches the new sections, the place names on the stay cards, the "Stays by area"
   list and the Tokyo lists to the language chosen in the page's language menu. Data: <script id="gsj-h15-data">,
   written by scripts/build-home-v15.py from config/home-v15.json. */
(() => {
  'use strict';
  const holder = document.getElementById('gsj-h15-data');
  if (!holder) return;
  let D;
  try { D = JSON.parse(holder.textContent); } catch (e) { return; }
  const LANGS = ['en', 'ja', 'ko', 'zh-TW'];
  const PREFIX = { en: '', ja: '/ja', ko: '/ko', 'zh-TW': '/zh-tw' };
  const pick = v => (LANGS.includes(v) ? v : null);
  const current = () => pick(document.getElementById('lang')?.value) || 'en';
  const word = (lang, key) => { const t = D.text[lang] || D.text.en; return key in t ? t[key] : D.text.en[key]; };
  const fill = (s, a) => (a ? s.replace(/\{(\w+)\}/g, (m, k) => (k in a ? String(a[k]) : m)) : s);
  const args = n => { try { return n.dataset.h15Args ? JSON.parse(n.dataset.h15Args) : null; } catch (e) { return null; } };
  const icon = name => `<svg aria-hidden="true" class="h15-i" focusable="false" viewBox="0 0 24 24"><use href="#h15-${name}"></use></svg>`;
  // English name for a place or area already shown in any language
  const reverse = map => {
    const out = {};
    for (const [en, names] of Object.entries(map)) { out[en] = en; for (const x of Object.values(names)) if (!(x in out)) out[x] = en; }
    return out;
  };
  const placeKey = reverse(D.places), areaKey = reverse(D.areas);

  function texts(lang) {
    document.querySelectorAll('[data-h15]').forEach(n => {
      const v = fill(word(lang, n.dataset.h15) ?? '', args(n));
      if (n.innerHTML !== v) n.innerHTML = v;
    });
    document.querySelectorAll('[data-h15-aria]').forEach(n => {
      n.setAttribute('aria-label', String(word(lang, n.dataset.h15Aria) || '').replace(/<[^>]*>/g, ''));
    });
    document.querySelectorAll('[data-h15-href]').forEach(a => {
      let v = D.links;
      for (const part of a.dataset.h15Href.split('.')) v = v == null ? v : v[part];
      if (v && typeof v === 'object') v = v[lang] ?? v.en;
      if (typeof v === 'string') a.setAttribute('href', v + (a.dataset.h15Suffix || ''));
    });
  }

  // "Popular group searches": the page's own script writes plain links here; draw the tiles again
  function tiles(lang) {
    const box = document.getElementById('seoGuideLinks');
    if (!box || (box.dataset.h15Lang === lang && box.querySelector('.h15-gt'))) return;
    const hrefs = D.links.guides[lang] || D.links.guides.en;
    box.innerHTML = hrefs.map((href, i) => {
      const art = i < 3
        ? `<span aria-hidden="true" class="h15-dots is-small is-dark">${`<span class="h15-dot">${icon('person')}</span>`.repeat([4, 6, 8][i])}</span>`
        : `<span aria-hidden="true" class="h15-gt-icons">${icon('kitchen')}${icon('washer')}</span>`;
      return `<a class="h15-gt" href="${href}" onclick="gaEvent('select_content',{content_type:'seo_guide',item_id:href})">${art}`
        + `<span class="h15-gt-row"><b class="h15-k">${word(lang, 'gu' + i)}</b><span class="h15-arrow is-dark">${icon('arrow')}</span></span></a>`;
    }).join('');
    box.dataset.h15Lang = lang;
  }

  // stay cards: place name and the link of the stay name
  function cards(lang) {
    document.querySelectorAll('#grid .card[data-id]').forEach(card => {
      const loc = card.querySelector('.loc');
      if (loc) {
        const key = placeKey[loc.dataset.h15Place || loc.textContent.trim()];
        if (key) {
          loc.dataset.h15Place = key;
          const v = lang === 'en' ? key : (D.places[key][lang] || key);
          if (loc.textContent !== v) loc.textContent = v;
        }
      }
      const a = card.querySelector('h3 a');
      if (a) {
        const v = PREFIX[lang] + '/stays/' + encodeURIComponent(card.dataset.id) + '/';
        if (a.getAttribute('href') !== v) a.setAttribute('href', v);
      }
    });
  }

  // "Stays by area": the area names (a new text node each time, so assets/gsj-ui.js leaves them as they are)
  function areas(lang) {
    document.querySelectorAll('#all-stays-directory summary').forEach(s => {
      const key = areaKey[s.dataset.h15Area || s.textContent.trim()];
      if (!key) return;
      s.dataset.h15Area = key;
      s.textContent = lang === 'en' ? key : (D.areas[key][lang] || key);
    });
  }

  // "Tokyo by group size": show only the list in the chosen language
  function lists(lang) {
    const box = document.querySelector('[data-h15-langlists]');
    if (!box) return;
    const want = lang === 'zh-TW' ? 'zh-Hant' : lang;
    const uls = [...box.querySelectorAll(':scope > ul[lang]')];
    if (!uls.some(u => u.getAttribute('lang') === want)) return;
    uls.forEach(u => { u.hidden = u.getAttribute('lang') !== want; });
  }

  function apply(lang) {
    lang = pick(lang) || current();
    texts(lang); tiles(lang); cards(lang); areas(lang); lists(lang);
  }
  apply();
  addEventListener('gsj-language', e => apply(e.detail));
  addEventListener('gsj-render', e => cards(pick(e.detail) || current()));
})();
