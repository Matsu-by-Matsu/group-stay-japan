#!/usr/bin/env python3
"""v16: fewer links to the hotels' official sites, so that visitors stay on GROUP STAY JAPAN.

Facility pages (stays/, ja/stays/, ko/stays/, zh-tw/stays/)
  - Keeps one source link per page: the line above the room cards
    ("Maximum official room capacity: N · Official source · date"), now shown in small grey text.
  - Removes the source link inside each room card.
  - Cleaning table: removes "Source · date" from each row.
Other pages (Tokyo 4/6/8 guests and longer stays, in every language)
  - Removes the table column whose cells are only links to official pages (the stay name already links to our page).
  - Removes "Source · date" from the cleaning tables and the "公式の客室仕様" links.
Photos keep their links: assets/gsj-ui.js opens them in the page's own photo viewer.
Every other link to an official site that is left opens in a new tab.
sitemap-core.xml, sitemap-stays-*.xml: lastmod of the pages that changed.
Run it last, after any script that rebuilds facility or Tokyo pages. Running it again changes nothing.
"""
import argparse
import datetime
import re
from pathlib import Path

SITE = 'https://groupstayjapan.synthx.jp'
OFF = r'https?://(?:www\.)?(?:mimaruhotels\.com|fav-hotels\.com|staytuned\.asia|grand-base\.jp)[^"]*'
OFF_A = re.compile(r'<a\b[^>]*\bhref="' + OFF + r'"[^>]*>')
SKIP_DIRS = {'.git', 'review', 'node_modules', 'data'}
SITEMAPS = ['sitemap-core.xml', 'sitemap-stays-en.xml', 'sitemap-stays-ja.xml', 'sitemap-stays-ko.xml', 'sitemap-stays-zh-tw.xml']
CARD = re.compile(r'<article class="room\b[^"]*"[^>]*>.*?</article>', re.S)
CARD_SRC = re.compile(r'<a href="' + OFF + r'" rel="noopener" target="_blank">[^<]*</a>')
PAGE_SRC = re.compile(r'<p>([^<]*<strong>\d+</strong> · <a href="' + OFF + r'" rel="noopener" target="_blank">[^<]*</a>)</p>')
ROW_SRC = re.compile(r'<a href="' + OFF + r'">(?:Source|出典|출처|來源)</a> · \d{4}-\d{2}-\d{2}')
SPEC_LINK = re.compile(r'<a href="' + OFF + r'"[^>]*>(?:公式の客室仕様|Official room specifications|공식 객실 사양|官方客房規格)[^<]*</a>(?:<br/>)?')
TABLE = re.compile(r'<table\b[^>]*>.*?</table>', re.S)
TR = re.compile(r'<tr\b[^>]*>.*?</tr>', re.S)
CELL = re.compile(r'<(t[hd])\b[^>]*>.*?</\1>', re.S)
OFF_CELL = re.compile(r'<td\b[^>]*>\s*(?:<a href="' + OFF + r'"[^>]*>[^<]*</a>)?\s*</td>', re.S)
SMALL = 'font-size:13px;line-height:1.5;color:#5d6b64'


def drop_official_column(table):
    rows = [[m.group(0) for m in CELL.finditer(r)] for r in TR.findall(table)]
    if len(rows) < 2 or len(rows[0]) < 2 or any(len(r) != len(rows[0]) for r in rows):
        return table
    for k in range(len(rows[0])):
        col = [r[k] for r in rows[1:]]
        if all(OFF_CELL.fullmatch(c) for c in col) and any(OFF_A.search(c) for c in col):
            def cut(m):
                cells = list(CELL.finditer(m.group(0)))
                s, e = cells[k].span()
                return m.group(0)[:s] + m.group(0)[e:]
            return TR.sub(cut, table)
    return table


def new_tab(m):
    a = m.group(0)
    if 'target=' in a or re.search(r'\.(?:jpe?g|png|webp|gif)"', a):
        return a  # photo links: the page's photo viewer opens them in place
    return a[:-1] + ' rel="noopener" target="_blank">'


def fix(text, facility):
    if facility:
        text = CARD.sub(lambda m: CARD_SRC.sub('', m.group(0)), text)
        text = PAGE_SRC.sub(lambda m: f'<p style="{SMALL}">' + m.group(1) + '</p>', text)
    else:
        text = TABLE.sub(lambda m: drop_official_column(m.group(0)), text)
        text = SPEC_LINK.sub('', text)
    text = ROW_SRC.sub('', text)
    return OFF_A.sub(new_tab, text)


def url_of(rel):
    return SITE + '/' + (rel[:-len('index.html')] if rel.endswith('index.html') else rel)


def main():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.datetime.now(jst).date().isoformat())
    ap.add_argument('--root', default=str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args()
    datetime.date.fromisoformat(a.date)
    root = Path(a.root)
    before = after = 0
    changed = {}
    for p in sorted(root.rglob('*.html')):
        rel = p.relative_to(root).as_posix()
        if set(rel.split('/')[:-1]) & SKIP_DIRS:
            continue
        old = p.read_bytes().decode('utf-8')
        n = len(OFF_A.findall(old))
        if not n:
            continue
        facility = re.fullmatch(r'(?:(?:ja|ko|zh-tw)/)?stays/[^/]+/index\.html', rel) is not None
        new = fix(old, facility)
        before += n
        after += len(OFF_A.findall(new))
        if new != old:
            changed[rel] = new
    locs = {url_of(rel) for rel in changed}
    maps = {}
    for name in SITEMAPS:
        path = root / name
        if path.exists():
            xml = path.read_bytes().decode('utf-8')
            new_xml = re.sub(r'(<loc>([^<]+)</loc>\s*<lastmod>)[^<]*(</lastmod>)',
                             lambda m: m.group(1) + a.date + m.group(3) if m.group(2) in locs else m.group(0), xml)
            if new_xml != xml:
                maps[name] = new_xml
    for rel, text in changed.items():
        (root / rel).write_bytes(text.encode('utf-8'))
    for name, xml in maps.items():
        (root / name).write_bytes(xml.encode('utf-8'))
    fac = sum(1 for r in changed if re.fullmatch(r'(?:(?:ja|ko|zh-tw)/)?stays/[^/]+/index\.html', r))
    print(f'pages changed: {len(changed)} (facility pages {fac}, other pages {len(changed) - fac}); '
          f'links to official sites: {before} -> {after}; sitemaps changed: {", ".join(maps) if maps else "none"}')


if __name__ == '__main__':
    main()
