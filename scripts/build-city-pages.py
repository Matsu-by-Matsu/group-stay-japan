#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the city pages for Osaka, Kyoto and Fukuoka (en, ko, zh-TW) and link them.

Usage (from the repository root or anywhere):
    python scripts/build-city-pages.py [--date YYYY-MM-DD] [--root PATH] [--pages-only]

Inputs : config/city-rooms.json   rooms of the hotels in the three cities (from the facility pages)
         config/city-pages.json   copy, labels and settings
         assets/gsj-readiness-levels.json   stay-length labels
Writes : en|ko|zh-tw/{osaka,kyoto,fukuoka}/index.html
Edits  : index.html, ko/index.html, zh-tw/index.html            links to the city pages
         stays/, ko/stays/, zh-tw/stays/ pages of these hotels  breadcrumb and BreadcrumbList get the city
         sitemap-core.xml and sitemap-stays-{en,ko,zh-tw}.xml   new URLs, lastmod of changed pages
Running it again on the same day gives the same files.
"""
import argparse
import datetime
import html
import json
import re
import sys
from pathlib import Path

ICONS = {
    'washer': 'M6.5 2.5h11A2.5 2.5 0 0 1 20 5v14a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 19V5a2.5 2.5 0 0 1 2.5-2.5zM7.5 13.5a4.5 4.5 0 1 0 9 0a4.5 4.5 0 1 0-9 0zM7.5 6h.01M10.5 6h3M9.6 14.1c.8-.5 1.6-.5 2.4 0s1.6.5 2.4 0',
    'drying': 'M9 3.5 4.5 5.5 2.5 9.5l3 1.5V20.5h13V11l3-1.5-2-4L15 3.5c-.5 1.3-1.6 2.1-3 2.1S9.5 4.8 9 3.5zM9.5 12.8c.8-.5 1.7-.5 2.5 0s1.7.5 2.5 0M9.5 16c.8-.5 1.7-.5 2.5 0s1.7.5 2.5 0',
    'kitchen': 'M4.5 10.5h15v5.5a4 4 0 0 1-4 4h-7a4 4 0 0 1-4-4v-5.5zM2.5 12.5h2M19.5 12.5h2M6 10.5c0-2.5 2.7-4.5 6-4.5s6 2 6 4.5M12 6V4',
    'microwave': 'M4.5 5h15a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zM6.5 8.5h7a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1v-5a1 1 0 0 1 1-1zM17.5 5v14M19.5 9h.01M19.5 12h.01',
    'person': 'M8.5 7.5a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0-7 0zM5.5 20c.6-3.6 3.2-5.8 6.5-5.8s5.9 2.2 6.5 5.8',
    'arrow': 'M5 12h14M13 6l6 6-6 6',
}
AMENITIES = ['washer', 'drying', 'kitchen', 'microwave']
SLASH = '<path d="M3 21 21 3"/>'
GA = ("<script>if(location.hostname==='groupstayjapan.synthx.jp'){window.dataLayer=window.dataLayer||[];"
      "window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-GVQ24M4R7R');"
      "const s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id=G-GVQ24M4R7R';"
      "document.head.appendChild(s)}</script><script src=\"/assets/gsj-attribution.js\"></script>")


def esc(value):
    return html.escape(str(value), quote=True)


class Build:
    def __init__(self, root, date):
        self.root = root
        self.date = date
        self.cfg = json.loads((root / 'config/city-pages.json').read_text(encoding='utf-8'))
        self.data = json.loads((root / 'config/city-rooms.json').read_text(encoding='utf-8'))
        self.levels = json.loads((root / 'assets/gsj-readiness-levels.json').read_text(encoding='utf-8'))['labels']
        self.site = self.cfg['site']
        self.changed = []

    # ---------- data ----------
    def hotels(self, city):
        return [p for p in self.data['properties'] if p['city'] == city]

    @staticmethod
    def spots(room, n):
        real = min(room['bedSleepers'], n)
        alt = min(room['otherSleepers'], n - real)
        return real, alt, n - real - alt

    def section(self, city, n):
        """Hotels with rooms for n or more guests, in display order, with totals."""
        out = []
        for p in self.hotels(city):
            rooms = []
            for i, r in enumerate(p['rooms']):
                if r['capacity'] < n:
                    continue
                real, alt, unk = self.spots(r, n)
                full = real == n
                washer = r['amenities']['washer'] == 'yes'
                key = (-(full and washer), -full, -washer, -r['level'], -(r['sizeM2'] or 0), i)
                rooms.append((key, r, real, alt, unk))
            if not rooms:
                continue
            rooms.sort(key=lambda x: x[0])
            both = sum(1 for _, r, real, _, _ in rooms if real == n and r['amenities']['washer'] == 'yes')
            full = sum(1 for _, _, real, _, _ in rooms if real == n)
            washer = sum(1 for _, r, _, _, _ in rooms if r['amenities']['washer'] == 'yes')
            out.append({'p': p, 'rooms': [x[1:] for x in rooms], 'both': both, 'full': full, 'washer': washer})
        out.sort(key=lambda h: (-h['both'], -h['full'], -h['washer'], h['p']['name'].lower()))
        totals = {
            'hotels': len(out),
            'rooms': sum(len(h['rooms']) for h in out),
            'full': sum(h['full'] for h in out),
            'washer': sum(h['washer'] for h in out),
            'unknown': any(unk for h in out for (_, _, _, unk) in h['rooms']),
        }
        return out, totals

    # ---------- rendering ----------
    def url(self, lang, city):
        return f"{self.site}/{self.cfg['languages'][lang]['dir']}/{city}/"

    def stay(self, lang, pid):
        return self.cfg['languages'][lang]['stayPath'].format(id=pid)

    def sprite(self):
        symbols = ''.join(f'<symbol id="gc-i-{k}" viewBox="0 0 24 24"><path d="{d}"/></symbol>' for k, d in ICONS.items())
        return f'<svg class="gc-sprite" aria-hidden="true" focusable="false">{symbols}</svg>'

    def chip(self, kind, state, T):
        icon = f'<use href="#gc-i-{kind}"/>'
        labels = T['amen'][kind]
        if state in ('yes', 'bathroom', 'ih'):
            label = labels.get(state, labels['yes'])
            return f'<span class="gc-chip gc-chip--yes"><svg aria-hidden="true" viewBox="0 0 24 24">{icon}</svg>{esc(label)}</span>'
        if state == 'no':
            return f'<span class="gc-chip gc-chip--no"><svg aria-hidden="true" viewBox="0 0 24 24">{icon}{SLASH}</svg>{esc(labels["no"])}</span>'
        return (f'<span class="gc-chip gc-chip--unk"><svg aria-hidden="true" viewBox="0 0 24 24">{icon}</svg>{esc(labels["yes"])}'
                f'<b aria-hidden="true">?</b><span class="gc-sr"> ({esc(T["unconfirmed"])})</span></span>')

    def row(self, lang, p, r, real, alt, unk, n, T):
        stay = self.stay(lang, p['id'])
        tokens = ('<span class="gc-t gc-t--real"><svg viewBox="0 0 24 24"><use href="#gc-i-person"/></svg></span>' * real
                  + '<span class="gc-t gc-t--alt"><svg viewBox="0 0 24 24"><use href="#gc-i-person"/></svg></span>' * alt
                  + '<span class="gc-t gc-t--unk"><svg viewBox="0 0 24 24"><use href="#gc-i-person"/></svg></span>' * unk)
        if real == n:
            verdict = f'<span class="gc-verdict gc-verdict--all">{esc(T["verdictAll"].format(n=n))}</span>'
        else:
            parts = [T['verdictSome'].format(n=n, real=real)]
            if alt:
                parts.append(T['verdictAlt'].format(alt=alt))
            if unk:
                parts.append(T['verdictUnk'].format(unk=unk))
            verdict = f'<span class="gc-verdict">{esc(" · ".join(parts))}</span>'
        meta = ' · '.join([T['capMax'].format(cap=r['capacityText'][lang]), r['size'], r['beds'][lang]])
        chips = ''.join(self.chip(k, r['amenities'][k], T) for k in AMENITIES)
        level = r['level']
        bars = ''.join('<i class="on"></i>' if i < level else '<i></i>' for i in range(4))
        stay_label = self.levels[self.cfg['languages'][lang]['levels']][level - 1]
        return (f'<li class="gc-room"><div class="gc-room-main"><a class="gc-room-name" data-stay="{esc(p["id"])}" '
                f'href="{esc(stay)}#{esc(r["id"])}">{esc(r["nameEn"])}</a><span class="gc-meta">{esc(meta)}</span></div>'
                f'<div class="gc-beds"><span aria-hidden="true" class="gc-tokens">{tokens}</span>{verdict}</div>'
                f'<div class="gc-feat"><div class="gc-amen">{chips}</div>'
                f'<span class="gc-stay"><span aria-hidden="true" class="gc-bars">{bars}</span>{esc(stay_label)}</span></div></li>')

    def hotel(self, lang, h, n, T, eager):
        p = h['p']
        stay = self.stay(lang, p['id'])
        limit = self.cfg['maxRoomsPerHotel']
        rows = ''.join(self.row(lang, p, r, real, alt, unk, n, T) for (r, real, alt, unk) in h['rooms'][:limit])
        more = ''
        if len(h['rooms']) > limit:
            text = T['more'].format(m=len(h['rooms']) - limit, n=n)
            more = f'<p class="gc-more"><a data-stay="{esc(p["id"])}" href="{esc(stay)}">{esc(text)}</a></p>'
        loading = 'eager' if eager else 'lazy'
        count = T['count'].format(n=n, k=len(h['rooms']), total=p['roomTypes'])
        photo = ''
        if p.get('photo'):
            photo = (f'<div class="gc-photo"><img alt="{esc(p["name"])}" decoding="async" height="224" loading="{loading}" '
                     f'src="{esc(p["photo"])}" width="336"/></div>')
        return (f'<article class="gc-hotel"><div class="gc-hotel-head">{photo}<div class="gc-hotel-text">'
                f'<p class="gc-sub">{esc(p["brand"])} · {esc(p["area"][lang])}</p>'
                f'<h3><a data-stay="{esc(p["id"])}" href="{esc(stay)}">{esc(p["name"])}</a></h3>'
                f'<p class="gc-count">{esc(count)}</p></div></div>'
                f'<ul class="gc-rooms">{rows}</ul>{more}'
                f'<a class="gc-all" data-stay="{esc(p["id"])}" href="{esc(stay)}">{esc(T["seeAll"].format(total=p["roomTypes"]))}'
                f'<svg aria-hidden="true" viewBox="0 0 24 24"><use href="#gc-i-arrow"/></svg></a></article>')

    def legend(self, T, unknown):
        items = ['<span><i class="gc-lg-real"></i>' + esc(T['legendReal']) + '</span>',
                 '<span><i class="gc-lg-alt"></i>' + esc(T['legendAlt']) + '</span>']
        if unknown:
            items.append('<span><i class="gc-lg-unk"></i>' + esc(T['legendUnk']) + '</span>')
        items += ['<i aria-hidden="true" class="gc-sep"></i>',
                  '<span><i class="gc-lg-yes"></i>' + esc(T['legendYes']) + '</span>',
                  '<span><i class="gc-lg-no"></i>' + esc(T['legendNo']) + '</span>',
                  '<span><i class="gc-lg-q"></i>' + esc(T['legendQ']) + '</span>']
        return '<div class="gc-legend">' + ''.join(items) + '</div>'

    def page(self, city, lang):
        L = self.cfg['languages'][lang]
        T = self.cfg['text'][lang]
        key = city['key']
        name = city['name'][lang]
        url = self.url(lang, key)
        sections = [(n,) + self.section(key, n) for n in self.cfg['groupSizes']]
        first_hotels, first_totals = sections[0][1], sections[0][2]
        title = T['title'].format(city=name)
        desc = T['description'].format(city=name, rooms=first_totals['rooms'], hotels=first_totals['hotels'])
        h1 = T['h1'].format(city=name)
        lead = T['lead']
        if city['leadExtra'][lang]:
            lead += ('' if lang == 'zh-TW' else ' ') + city['leadExtra'][lang]
        home = L['home']

        alternates = ''.join(
            f'<link href="{esc(self.url(lg, key))}" hreflang="{esc(self.cfg["languages"][lg]["hreflang"])}" rel="alternate"/>'
            for lg in self.cfg['languages'])
        alternates += f'<link href="{esc(self.url("en", key))}" hreflang="x-default" rel="alternate"/>'
        og_image = first_hotels[0]['p']['photo'] if first_hotels and first_hotels[0]['p'].get('photo') else f'{self.site}/assets/hero.jpg'
        items = [{'@type': 'ListItem', 'position': i + 1, 'name': h['p']['name'], 'url': self.site + self.stay(lang, h['p']['id'])}
                 for i, h in enumerate(first_hotels)]
        ld = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'CollectionPage', 'name': h1, 'description': desc, 'url': url, 'inLanguage': L['hreflang'],
             'dateModified': self.date, 'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(items), 'itemListElement': items}},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': T['home'], 'item': self.site + home},
                {'@type': 'ListItem', 'position': 2, 'name': name, 'item': url}]}]}
        ld_text = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')

        langs = ''
        for lg, info in self.cfg['languages'].items():
            current = ' aria-current="page"' if lg == lang else ''
            langs += (f'<a{current} href="/{info["dir"]}/{key}/" lang="{info["htmlLang"]}">'
                      f'{esc(info["langLabel"])}</a>')
        tabs = ''
        for i, (n, _, _) in enumerate(sections):
            current = ' aria-current="true"' if i == 0 else ''
            tabs += f'<a{current} href="#for-{n}">{esc(T["tab"].format(n=n))}</a>'

        body_sections = []
        first_card = True
        for n, hotels, totals in sections:
            cards = []
            for h in hotels:
                cards.append(self.hotel(lang, h, n, T, first_card))
                first_card = False
            stats = (f'<div class="gc-stats"><div class="gc-stat"><b>{totals["hotels"]}</b><span>{esc(T["statHotels"])}</span></div>'
                     f'<div class="gc-stat"><b>{totals["rooms"]}</b><span>{esc(T["statRooms"])}</span></div>'
                     f'<div class="gc-stat gc-stat--hl"><b>{totals["full"]}</b><span>{esc(T["statAll"].format(n=n))}</span></div>'
                     f'<div class="gc-stat gc-stat--hl"><b>{totals["washer"]}</b><span>{esc(T["statWasher"])}</span></div></div>')
            intro = T['sectionIntro'].format(rooms=totals['rooms'], hotels=totals['hotels'], n=n)
            body_sections.append(
                f'<section aria-labelledby="for-{n}-title" class="gc-section" id="for-{n}">'
                f'<h2 id="for-{n}-title">{esc(T["sectionTitle"].format(n=n))}</h2><p class="gc-intro">{esc(intro)}</p>'
                f'{stats}{self.legend(T, totals["unknown"])}<div class="gc-hotels">{"".join(cards)}</div></section>')

        others = ' '.join(f'<a href="/{L["dir"]}/{c["key"]}/">{esc(c["name"][lang])}</a>'
                          for c in self.cfg['cities'] if c['key'] != key)
        tokyo = ' · '.join(f'<a href="{esc(self.cfg["tokyoLists"][lang][str(n)])}">{esc(T["tokyoTab"].format(n=n))}</a>'
                           for n in self.cfg['groupSizes'])
        more_cities = (f'<nav aria-label="{esc(T["otherCities"])}" class="gc-more-cities"><b>{esc(T["otherCities"])}</b>'
                       f'{others}<span>{esc(T["tokyo"])} {tokyo}</span></nav>')

        script = ("(function(){var s=[].slice.call(document.querySelectorAll('.gc-section')),"
                  "t=[].slice.call(document.querySelectorAll('.gc-tabs a'));if(!s.length)return;"
                  "function show(id){if(!s.some(function(x){return x.id===id}))id=s[0].id;"
                  "s.forEach(function(x){x.hidden=x.id!==id});t.forEach(function(a){if(a.getAttribute('href')==='#'+id)"
                  "a.setAttribute('aria-current','true');else a.removeAttribute('aria-current')})}"
                  "t.forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();"
                  "var id=a.getAttribute('href').slice(1);if(history.replaceState)history.replaceState(null,'','#'+id);show(id);"
                  f"if(window.GSJTracking)window.GSJTracking.event('select_content',{{content_type:'city_tab',item_id:id,seo_theme:'city_{key}',language:'{lang}'}})"
                  "})});show(location.hash.slice(1));window.addEventListener('hashchange',function(){show(location.hash.slice(1))})})();"
                  "document.querySelectorAll('[data-stay]').forEach(function(a){a.addEventListener('click',function(){"
                  f"if(window.GSJTracking)window.GSJTracking.event('select_content',{{content_type:'seo_stay',item_id:a.dataset.stay,seo_theme:'city_{key}',language:'{lang}'}})"
                  "})});")

        return ('<!DOCTYPE html>\n'
                f'<html lang="{L["htmlLang"]}"><head><meta charset="utf-8"/><meta content="width=device-width,initial-scale=1" name="viewport"/>'
                f'{GA}<title>{esc(title)}</title><meta content="{esc(desc)}" name="description"/>'
                '<meta content="index,follow,max-image-preview:large" name="robots"/>'
                f'<link href="{esc(url)}" rel="canonical"/>{alternates}'
                f'<meta content="website" property="og:type"/><meta content="{esc(title)}" property="og:title"/>'
                f'<meta content="{esc(desc)}" property="og:description"/><meta content="{esc(url)}" property="og:url"/>'
                f'<meta content="{esc(og_image)}" property="og:image"/><meta content="summary_large_image" name="twitter:card"/>'
                f'<script type="application/ld+json">{ld_text}</script>'
                f'<link href="{esc(self.cfg["css"])}" rel="stylesheet"/></head>'
                f'<body class="gc">{self.sprite()}'
                f'<header class="gc-top"><div class="gc-wrap"><a class="gc-brand" href="{esc(home)}">GROUP STAY JAPAN</a>'
                f'<nav aria-label="{esc(T["langsAria"])}" class="gc-langs">{langs}</nav></div></header>'
                f'<section class="gc-hero"><div class="gc-wrap">'
                f'<nav aria-label="{esc(T["crumbsAria"])}" class="gc-crumbs"><a href="{esc(home)}">{esc(T["home"])}</a> › {esc(name)}</nav>'
                f'<p class="gc-eyebrow">{esc(T["eyebrow"].format(city=name))}</p><h1>{esc(h1)}</h1>'
                f'<p class="gc-lead">{esc(lead)}</p><nav aria-label="{esc(T["tabsAria"])}" class="gc-tabs">{tabs}</nav></div></section>'
                f'<main class="gc-main"><div class="gc-wrap">{"".join(body_sections)}'
                f'<div class="gc-notes"><p>{esc(T["bedNote"])}</p><p>{esc(T["dataNote"])}</p></div>{more_cities}</div></main>'
                f'<footer class="gc-foot"><div class="gc-wrap"><div><a href="{esc(home)}">{esc(T["footHome"])}</a>'
                f'<p>{esc(T["footDisclosure"])}</p></div><a href="/_SYSTEM/about.html">{esc(T["footAbout"])}</a></div></footer>'
                f'<script>{script}</script></body></html>\n')

    # ---------- files ----------
    def write(self, rel, text):
        path = self.root / rel
        old = path.read_text(encoding='utf-8') if path.exists() else None
        if old != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8', newline='\n')
            self.changed.append(rel)
        return old != text

    def build_pages(self):
        for city in self.cfg['cities']:
            for lang in self.cfg['languages']:
                rel = f"{self.cfg['languages'][lang]['dir']}/{city['key']}/index.html"
                self.write(rel, self.page(city, lang))

    def edit_home_en(self):
        rel = 'index.html'
        s = (self.root / rel).read_text(encoding='utf-8')
        if '<!-- gsj-home-v15:start -->' in s:
            return False  # v15: the top page has its own city links (scripts/build-home-v15.py)
        T = self.cfg['text']['en']
        links = ''.join(f'<li><a href="/en/{c["key"]}/">{esc(T["homeLink"].format(city=c["name"]["en"]))}</a></li>'
                        for c in self.cfg['cities'])
        block = (f'<!-- gsj-city-pages --><h3 style="margin-top:22px">{esc(T["homeLinksTitle"])}</h3>'
                 f'<ul class="gsj-home-beds-links">{links}</ul><!-- /gsj-city-pages -->')
        if '<!-- gsj-city-pages -->' in s:
            s = re.sub(r'<!-- gsj-city-pages -->.*?<!-- /gsj-city-pages -->', lambda m: block, s, count=1, flags=re.S)
        else:
            i = s.index('data-i18n="realBedsTokyo"')
            j = s.index('</ul>', i) + len('</ul>')
            s = s[:j] + block + s[j:]
        return self.write(rel, s)

    def edit_home_locale(self, lang):
        L = self.cfg['languages'][lang]
        T = self.cfg['text'][lang]
        rel = f"{L['dir']}/index.html"
        s = (self.root / rel).read_text(encoding='utf-8')
        for c in self.cfg['cities']:
            name = c['name'][lang]
            para = (f'<p data-city-page="{c["key"]}" style="margin:6px 0 4px"><a href="/{L["dir"]}/{c["key"]}/" '
                    f'style="font-weight:700">{esc(T["homeLink"].format(city=name))}</a></p>')
            if f'data-city-page="{c["key"]}"' in s:
                s = re.sub(r'<p data-city-page="' + c['key'] + r'".*?</p>', lambda m: para, s, count=1, flags=re.S)
            else:
                m = re.search(r'<h3>' + re.escape(name) + r'\s?[（(]\d+[^<]*</h3>', s)
                if not m:
                    sys.exit(f'{rel}: heading for {name} not found')
                s = s[:m.end()] + para + s[m.end():]
        return self.write(rel, s)

    def edit_stay(self, lang, pid, city):
        L = self.cfg['languages'][lang]
        T = self.cfg['text'][lang]
        rel = L['stayPath'].format(id=pid).strip('/') + '/index.html'
        s = (self.root / rel).read_text(encoding='utf-8')
        name = city['name'][lang]
        link = f'/{L["dir"]}/{city["key"]}/'
        head = (f'<nav aria-label="Breadcrumb" class="gsj-v7-breadcrumb"><a href="{L["home"]}">'
                f'{html.escape(T["home"], quote=False)}</a> › ')
        if s.count(head) != 1:
            sys.exit(f'{rel}: breadcrumb not found exactly once')
        crumb = f'<a href="{link}">{html.escape(name, quote=False)}</a> › '
        i = s.index(head) + len(head)
        if not s.startswith(crumb, i):
            s = s[:i] + crumb + s[i:]
        blocks = [m for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, flags=re.S)
                  if '"BreadcrumbList"' in m.group(1)]
        if len(blocks) != 1:
            sys.exit(f'{rel}: BreadcrumbList not found exactly once')
        m = blocks[0]
        obj = json.loads(m.group(1))
        if json.dumps(obj, ensure_ascii=False) != m.group(1):
            sys.exit(f'{rel}: BreadcrumbList is not in the expected format')
        items = obj['itemListElement']
        url = self.site + link
        if not any(it.get('item') == url for it in items):
            items.insert(1, {'@type': 'ListItem', 'position': 2, 'name': name, 'item': url})
            for k, it in enumerate(items):
                it['position'] = k + 1
            s = s[:m.start(1)] + json.dumps(obj, ensure_ascii=False) + s[m.end(1):]
        return self.write(rel, s)

    def sitemap(self, rel, update=(), ensure=()):
        """Add missing URLs (ensure) and set lastmod of changed pages (update)."""
        path = self.root / rel
        s = path.read_text(encoding='utf-8')
        for url in ensure:
            if f'<loc>{url}</loc>' not in s:
                s = s.replace('</urlset>', f'<url><loc>{url}</loc><lastmod>{self.date}</lastmod></url></urlset>', 1)
        for url in update:
            pat = re.compile(r'(<url><loc>' + re.escape(url) + r'</loc><lastmod>)([^<]*)(</lastmod></url>)')
            if not pat.search(s):
                sys.exit(f'{rel}: {url} not found')
            s = pat.sub(lambda m: m.group(1) + self.date + m.group(3), s, count=1)
        self.write(rel, s)

    def run(self, pages_only=False):
        self.build_pages()
        if pages_only:
            return
        home_changed = {'en': self.edit_home_en()}
        for lang in ('ko', 'zh-TW'):
            home_changed[lang] = self.edit_home_locale(lang)
        stays_changed = {lang: [] for lang in self.cfg['languages']}
        cities = {c['key']: c for c in self.cfg['cities']}
        for p in self.data['properties']:
            for lang in self.cfg['languages']:
                if self.edit_stay(lang, p['id'], cities[p['city']]):
                    stays_changed[lang].append(p['id'])
        city_urls = [self.url(lang, c['key']) for c in self.cfg['cities'] for lang in self.cfg['languages']]
        changed_city = [u for u in city_urls if u.replace(self.site + '/', '') + 'index.html' in self.changed]
        homes = [self.site + self.cfg['languages'][lg]['home'] for lg, ch in home_changed.items() if ch]
        self.sitemap('sitemap-core.xml', update=changed_city + homes, ensure=city_urls)
        for lang, ids in stays_changed.items():
            if ids:
                rel = f"sitemap-stays-{self.cfg['languages'][lang]['dir']}.xml"
                self.sitemap(rel, update=[self.site + self.stay(lang, pid) for pid in ids])

    def summary(self):
        print('city     size hotels rooms all-in-real-beds in-room-washer rows-shown')
        for c in self.cfg['cities']:
            for n in self.cfg['groupSizes']:
                hotels, t = self.section(c['key'], n)
                shown = sum(min(len(h['rooms']), self.cfg['maxRoomsPerHotel']) for h in hotels)
                first = hotels[0]['p']['name'] if hotels else '-'
                print(f"{c['key']:8s} {n:4d} {t['hotels']:6d} {t['rooms']:5d} {t['full']:16d} {t['washer']:14d} {shown:10d}  first: {first}")
        print(f'{len(self.changed)} files written or changed')
        for rel in self.changed:
            print('  ' + rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.date.today().isoformat())
    ap.add_argument('--root', default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument('--pages-only', action='store_true')
    args = ap.parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.date):
        sys.exit('--date must be YYYY-MM-DD')
    b = Build(Path(args.root), args.date)
    b.run(pages_only=args.pages_only)
    b.summary()


if __name__ == '__main__':
    main()
