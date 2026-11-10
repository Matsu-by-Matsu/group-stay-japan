#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Redesign the room cards on the facility pages (en, ja, ko, zh-TW).

Usage (from the repository root or anywhere):
    python scripts/apply-room-cards.py [--date YYYY-MM-DD] [--root PATH] [--only ID,ID]

Inputs : config/room-cards.json         card data for every room in every language (taken from the old cards)
         config/room-card-labels.json   labels of the new cards
Edits  : stays/, ja/stays/, ko/stays/, zh-tw/stays/   room cards, CSS link, icon sprite, card grid
         sitemap-stays-{en,ja,ko,zh-tw}.xml          lastmod of changed pages
An old card is replaced only when it is exactly the card the data was taken from (MD5).
Otherwise the script stops without writing that page. Running it again gives the same files.
"""
import argparse
import datetime
import hashlib
import html
import json
import re
import sys
from pathlib import Path

LANGS = {
    'en': {'dir': 'stays', 'sitemap': 'sitemap-stays-en.xml', 'path': '/stays/'},
    'ja': {'dir': 'ja/stays', 'sitemap': 'sitemap-stays-ja.xml', 'path': '/ja/stays/'},
    'ko': {'dir': 'ko/stays', 'sitemap': 'sitemap-stays-ko.xml', 'path': '/ko/stays/'},
    'zh-TW': {'dir': 'zh-tw/stays', 'sitemap': 'sitemap-stays-zh-tw.xml', 'path': '/zh-tw/stays/'},
}
SITE = 'https://groupstayjapan.synthx.jp'
ICONS = {
    'washer': 'M6.5 2.5h11A2.5 2.5 0 0 1 20 5v14a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 19V5a2.5 2.5 0 0 1 2.5-2.5zM7.5 13.5a4.5 4.5 0 1 0 9 0a4.5 4.5 0 1 0-9 0zM7.5 6h.01M10.5 6h3M9.6 14.1c.8-.5 1.6-.5 2.4 0s1.6.5 2.4 0',
    'drying': 'M9 3.5 4.5 5.5 2.5 9.5l3 1.5V20.5h13V11l3-1.5-2-4L15 3.5c-.5 1.3-1.6 2.1-3 2.1S9.5 4.8 9 3.5zM9.5 12.8c.8-.5 1.7-.5 2.5 0s1.7.5 2.5 0M9.5 16c.8-.5 1.7-.5 2.5 0s1.7.5 2.5 0',
    'kitchen': 'M4.5 10.5h15v5.5a4 4 0 0 1-4 4h-7a4 4 0 0 1-4-4v-5.5zM2.5 12.5h2M19.5 12.5h2M6 10.5c0-2.5 2.7-4.5 6-4.5s6 2 6 4.5M12 6V4',
    'microwave': 'M4.5 5h15a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zM6.5 8.5h7a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1v-5a1 1 0 0 1 1-1zM17.5 5v14M19.5 9h.01M19.5 12h.01',
    'fridge': 'M8 2.5h8a2.5 2.5 0 0 1 2.5 2.5v14a2.5 2.5 0 0 1-2.5 2.5H8A2.5 2.5 0 0 1 5.5 19V5A2.5 2.5 0 0 1 8 2.5zM5.5 10h13M8.5 6v1.5M8.5 13v3',
    'stove': 'M5.5 4h13A2.5 2.5 0 0 1 21 6.5v11a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5v-11A2.5 2.5 0 0 1 5.5 4zM5.5 10.5a3 3 0 1 0 6 0a3 3 0 1 0-6 0zM12.5 10.5a3 3 0 1 0 6 0a3 3 0 1 0-6 0zM7 16.5h.01M12 16.5h.01M17 16.5h.01',
    'cookware': 'M2.5 12a6.5 6.5 0 1 0 13 0a6.5 6.5 0 1 0-13 0zM15.5 12h6',
    'tableware': 'M6.5 3v5a2.5 2.5 0 0 0 5 0V3M9 3v5.5M9 10.5V21M17.5 21V3c-2 1.6-3 4.2-3 7.5V13h3',
    'person': 'M8.5 7.5a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0-7 0zM5.5 20c.6-3.6 3.2-5.8 6.5-5.8s5.9 2.2 6.5 5.8',
    'check': 'M5 12.5l4.5 4.5L19 7.5',
    'info': 'M3 12a9 9 0 1 0 18 0a9 9 0 1 0-18 0zM12 11v5M12 7.5h.01',
    'bed': 'M3 7v12M3 15h18v4M21 15v-2.5A2.5 2.5 0 0 0 18.5 10H10v5M5.5 12.5h2.5',
    'bunk': 'M5 3v18M19 3v18M5 9h14M5 17h14M7.5 6.5h3M7.5 14.5h3',
    'futon': 'M2.5 17.5h19M3.5 17.5v-3a1.5 1.5 0 0 1 1.5-1.5h14a1.5 1.5 0 0 1 1.5 1.5v3M6 13v-1.5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1V13',
    'sofa': 'M4.5 11V8.5A2.5 2.5 0 0 1 7 6h10a2.5 2.5 0 0 1 2.5 2.5V11M3 11h18v6.5H3zM5 17.5v2M19 17.5v2M7.5 14h9',
}
TILES = ['washer', 'drying', 'kitchen', 'microwave', 'fridge', 'stove', 'cookware', 'tableware']
SLASH = '<path d="M3 21 21 3"/>'
ARTICLE = r'<article class="room(?: rc)?"(?: data-readiness-level="\d")? id="{rid}">.*?</article>'


def esc(value):
    return html.escape(str(value), quote=True)


def icon(name, extra=''):
    return f'<svg aria-hidden="true" viewBox="0 0 24 24"><use href="#rc-i-{name}"/>{extra}</svg>'


def sprite():
    symbols = ''.join(f'<symbol id="rc-i-{k}" viewBox="0 0 24 24"><path d="{d}"/></symbol>' for k, d in ICONS.items())
    return f'<svg aria-hidden="true" class="rc-sprite" focusable="false">{symbols}</svg>'


def render(room, lang, L, details):
    t = room['text'][lang]
    cap = room['capacity']
    out = [f'<article class="room rc" data-readiness-level="{room["level"]}" id="{room["id"]}">']

    # name
    out.append('<div class="rc-head">' + t['h2'] + (t['official'] or '') + '</div>')

    # numbers
    stats = [f'<div class="rc-stat"><b>{cap}</b><span>{esc(L["cap"]["adults" if room["adults"] else "guests"])}</span></div>']
    size = room['size']
    if size:
        if size['kind'] == 'text':
            stats.append(f'<div class="rc-stat rc-stat--text"><b>{esc(size["value"])}</b><span>{esc(L["sizeText"])}</span></div>')
        else:
            stats.append(f'<div class="rc-stat"><b>{esc(size["value"])}</b><span>{esc(L["size"])}</span></div>')
    if room['perGuest']:
        stats.append(f'<div class="rc-stat"><b>{esc(room["perGuest"])}</b><span>{esc(L["perGuest"])}</span></div>')
    kind = ' rc-stats--2' if len(stats) == 2 else ''
    out.append(f'<div class="rc-stats{kind}">' + ''.join(stats) + '</div>')
    if t['extra']:
        out.append('<div class="rc-extra">' + ''.join(f'<span>{esc(x)}</span>' for x in t['extra']) + '</div>')
    for note in t['notes']:
        out.append(f'<p class="rc-note">{esc(note)}</p>')

    # beds
    notes = []
    if room['bedStatus'] != 'ok':
        real, alt, unk = 0, 0, cap
        verdict = f'<span class="rc-verdict rc-verdict--check">{icon("info")}{esc(L["verdictCheck"])}</span>'
    else:
        real = min(room['bedSleepers'], cap)
        alt = min(room['otherSleepers'], cap - real)
        unk = cap - real - alt
        if real == cap:
            text = (L['verdictBoth'] if cap == 2 else L['verdictAll']).format(n=cap)
            verdict = f'<span class="rc-verdict rc-verdict--all">{icon("check")}{esc(text)}</span>'
        else:
            text = L['verdictSome'].format(n=cap, real=real)
            verdict = f'<span class="rc-verdict">{icon("info")}{esc(text)}</span>'
            if alt:
                notes.append(L['noteAlt'].format(alt=alt))
            if unk:
                notes.append(L['noteUnk'].format(n=cap))
    tokens = ''.join(['<i class="rc-t rc-t--real">' + icon('person') + '</i>'] * real
                     + ['<i class="rc-t rc-t--alt">' + icon('person') + '</i>'] * alt
                     + ['<i class="rc-t rc-t--unk">' + icon('person') + '</i>'] * unk)
    items = t['bedItems']
    if items and room['bedTypes'] and len(items) == len(room['bedTypes']):
        beds = ''
        for item, kind_ in zip(items, room['bedTypes']):
            cls = ' class="rc-bed--alt"' if kind_ in ('futon', 'sofa') else ''
            beds += f'<li{cls}>{icon(kind_)}{esc(item)}</li>'
    else:
        beds = f'<li>{icon("bed")}{esc(t["beds"])}</li>'
    out.append('<div class="rc-beds"><div class="rc-beds-top">'
               f'<span class="rc-label">{esc(L["beds"])}</span>{verdict}</div>'
               f'<div aria-hidden="true" class="rc-tokens">{tokens}</div>'
               + ''.join(f'<p class="rc-alt">{esc(n)}</p>' for n in notes)
               + f'<ul class="rc-bedlist">{beds}</ul></div>')

    # in the room
    tiles = []
    for key in TILES:
        state = room['amenities'][key]
        labels = L['tiles'][key]
        if state in ('yes', 'bathroom', 'ih'):
            label = labels[2] if state in ('bathroom', 'ih') else labels[0]
            more = f'<small>{esc(L["freezer"])}</small>' if key == 'fridge' and room['freezer'] else ''
            tiles.append(f'<li class="rc-tile rc-tile--yes">{icon(key)}<span>{esc(label)}{more}</span></li>')
        elif state == 'no':
            tiles.append(f'<li class="rc-tile rc-tile--no">{icon(key, SLASH)}<span>{esc(labels[1])}</span></li>')
        else:
            tiles.append(f'<li class="rc-tile rc-tile--unk"><b aria-hidden="true">?</b>{icon(key)}'
                         f'<span>{esc(labels[0])}<span class="rc-sr"> ({esc(L["unconfirmed"])})</span></span></li>')
    legend = ('<p class="rc-legend">'
              f'<span><i aria-hidden="true" class="rc-lg-yes"></i>{esc(L["legend"][0])}</span>'
              f'<span><i aria-hidden="true" class="rc-lg-no"></i>{esc(L["legend"][1])}</span>'
              f'<span><i aria-hidden="true" class="rc-lg-q"></i>{esc(L["legend"][2])}</span></p>')
    level = room['level']
    bars = ''.join('<i class="on"></i>' if i < level else '<i></i>' for i in range(4))
    labels = ''.join(f'<span class="on">{esc(x)}</span>' if i == level - 1 else f'<span>{esc(x)}</span>'
                     for i, x in enumerate(L['stayBars']))
    out.append('<div class="rc-panel">'
               f'<p class="rc-panel-title">{esc(L["panel"])}</p><ul class="rc-tiles">{"".join(tiles)}</ul>{legend}'
               f'<div class="rc-stay"><p class="rc-stay-top"><span>{esc(L["stayTitle"])}</span><b>{esc(L["stayValue"][level - 1])}</b></p>'
               f'<div aria-hidden="true" class="rc-bars">{bars}</div><div aria-hidden="true" class="rc-bar-labels">{labels}</div></div></div>')

    # size compared with other rooms
    if t['sizeTitle']:
        cmp_ = room['sizeCompare']
        bars = ''
        if cmp_:
            bars = ('<div class="rc-size-bars">'
                    f'<span>{esc(L["thisRoom"])}</span><i><b style="width:{cmp_["thisPct"]}%"></b></i><strong>{esc(size["value"])} m²</strong>'
                    f'<span>{esc(L["average"])}</span><i class="rc-avg"><b style="width:{cmp_["avgPct"]}%"></b></i>'
                    f'<strong class="rc-avg">{esc(cmp_["avg"])} m²</strong></div>')
        items = ''.join(f'<li>{esc(x)}</li>' for x in t['sizeItems'])
        out.append(f'<div class="size-comparison rc-size"><h3>{esc(t["sizeTitle"])}</h3>{bars}<ul>{items}</ul></div>')

    out.append(details)
    out.append('</article>')
    return ''.join(out)


class Apply:
    def __init__(self, root, date, only):
        self.root = root
        self.date = date
        self.data = json.loads((root / 'config/room-cards.json').read_text(encoding='utf-8'))['properties']
        self.labels = json.loads((root / 'config/room-card-labels.json').read_text(encoding='utf-8'))
        self.only = only
        self.changed = {lang: [] for lang in LANGS}
        self.cards = 0

    def page(self, pid, lang, rooms):
        rel = f"{LANGS[lang]['dir']}/{pid}/index.html"
        path = self.root / rel
        s = path.read_text(encoding='utf-8')
        old = s
        L = self.labels[lang]
        for room in rooms:
            pat = re.compile(ARTICLE.format(rid=re.escape(room['id'])), re.S)
            found = list(pat.finditer(s))
            if len(found) != 1:
                sys.exit(f'{rel}: {room["id"]} found {len(found)} times')
            m = found[0]
            article = m.group(0)
            if article.startswith('<article class="room" ') and hashlib.md5(article.encode('utf-8')).hexdigest() != room['text'][lang]['hash']:
                sys.exit(f'{rel}: {room["id"]} is not the card the data was taken from (changed since 2026-11-09)')
            details = re.findall(r'<details>.*?</details>', article, flags=re.S)
            if len(details) != 1:
                sys.exit(f'{rel}: {room["id"]} has {len(details)} <details>')
            s = s[:m.start()] + render(room, lang, L, details[0]) + s[m.end():]
            self.cards += 1
        # one grid around the cards
        spans = [m.span() for m in re.finditer(r'<article class="room rc".*?</article>', s, flags=re.S)]
        first, last = spans[0][0], spans[-1][1]
        if not s[:first].endswith('<div class="rc-grid">'):
            middle = s[first:last]
            if re.sub(r'<article class="room rc".*?</article>', '', middle, flags=re.S).strip():
                sys.exit(f'{rel}: something other than room cards between the cards')
            s = s[:first] + '<div class="rc-grid">' + middle + '</div>' + s[last:]
        # stylesheet and icons
        css = f'<link href="{self.labels["css"]}" rel="stylesheet"/>'
        if 'gsj-room-cards.css' not in s:
            s = s.replace('</head>', css + '</head>', 1)
        else:
            s = re.sub(r'<link href="/assets/gsj-room-cards\.css[^"]*" rel="stylesheet"/>', lambda _: css, s, count=1)
        if 'class="rc-sprite"' not in s:
            s = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + sprite(), s, count=1)
        else:
            s = re.sub(r'<svg aria-hidden="true" class="rc-sprite".*?</svg>', lambda _: sprite(), s, count=1, flags=re.S)
        if s != old:
            path.write_text(s, encoding='utf-8', newline='\n')
            self.changed[lang].append(pid)

    def sitemaps(self):
        for lang, ids in self.changed.items():
            if not ids:
                continue
            rel = LANGS[lang]['sitemap']
            path = self.root / rel
            s = path.read_text(encoding='utf-8')
            for pid in ids:
                url = SITE + LANGS[lang]['path'] + pid + '/'
                pat = re.compile(r'(<url><loc>' + re.escape(url) + r'</loc><lastmod>)([^<]*)(</lastmod></url>)')
                if not pat.search(s):
                    sys.exit(f'{rel}: {url} not found')
                s = pat.sub(lambda m: m.group(1) + self.date + m.group(3), s, count=1)
            path.write_text(s, encoding='utf-8', newline='\n')

    def run(self):
        for pid, rooms in self.data.items():
            if self.only and pid not in self.only:
                continue
            for lang in LANGS:
                self.page(pid, lang, rooms)
        self.sitemaps()
        total = sum(len(v) for v in self.changed.values())
        print(f'{self.cards} cards built; pages changed: ' + ', '.join(f'{k} {len(v)}' for k, v in self.changed.items()) + f' (total {total})')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.date.today().isoformat())
    ap.add_argument('--root', default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument('--only', default='', help='comma-separated facility ids (for testing)')
    args = ap.parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.date):
        sys.exit('--date must be YYYY-MM-DD')
    only = set(x for x in args.only.split(',') if x)
    Apply(Path(args.root), args.date, only).run()


if __name__ == '__main__':
    main()
