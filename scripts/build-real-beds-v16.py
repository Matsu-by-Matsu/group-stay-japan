#!/usr/bin/env python3
"""Data article redesign (v16): rebuilds the body of /en/real-beds/ and /ja/real-beds/ in the top page's design.

Reads config/home-v15.json (shared texts, numbers, links) and config/real-beds-v16.json (texts and numbers of
this article), and uses the drawing helpers of scripts/build-home-v15.py.

en/real-beds/index.html, ja/real-beds/index.html
  - Replaces everything inside <main> (the breadcrumb is kept as it is).
  - Adds assets/gsj-home-v15.css and assets/gsj-real-beds.css to <head>.
  - title, meta description, canonical, hreflang, JSON-LD, GA, header and footer are not changed.
sitemap-core.xml
  - lastmod of the pages that changed.
Every number is checked before anything is written. Running it again changes nothing.
"""
import argparse
import datetime
import importlib.util
import json
import re
from pathlib import Path

SITE = 'https://groupstayjapan.synthx.jp'
PAGES = {'en': 'en/real-beds/index.html', 'ja': 'ja/real-beds/index.html'}


def load_v15(root):
    spec = importlib.util.spec_from_file_location('build_home_v15', root / 'scripts/build-home-v15.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_numbers(cfg, rb):
    hotels, rooms, real, short, check = cfg['numbers']['total']
    n = rb['numbers']
    ok = (sum(r for _, r, _ in n['groups']) == rooms and sum(k for _, _, k in n['groups']) == real
          and short == n['rest']['rooms'] and sum(c for _, c in n['gaps']) == short
          and rooms == real + short + check
          and sum(c for _, c in n['six']) == dict((g, r) for g, r, _ in n['groups'])['6']
          and dict(n['six'])['6'] == dict((g, k) for g, _, k in n['groups'])['6']
          and sum(a[2] for a in cfg['numbers']['areas']) == rooms and sum(a[3] for a in cfg['numbers']['areas']) == real)
    if not ok:
        raise SystemExit('numbers in config/home-v15.json and config/real-beds-v16.json do not add up; nothing was written')


class Article:
    def __init__(self, v, cfg, rb, lang):
        self.v, self.B, self.lang = v, v.Block(cfg, lang, False), lang
        self.rt, self.n = rb['text'], rb['numbers']
        self.cn = cfg['numbers']

    def r(self, key, **args):
        s = self.rt[key][self.lang]
        for k, val in args.items():
            s = s.replace('{' + k + '}', str(val))
        return s

    def t(self, key, tag='span', cls='', **args):
        c = f' class="{cls}"' if cls else ''
        return f'<{tag}{c}>{self.r(key, **args)}</{tag}>'

    def hero(self):
        B, v = self.B, self.v
        hotels, rooms, real, short, check = self.cn['total']
        pct = round(real / rooms * 100)
        return ('<section aria-labelledby="rbTitle" class="h15 h15-beds rb-hero" id="real-beds"><div class="h15-wrap h15-stack-lg">'
                '<div class="h15-beds-top"><div class="h15-beds-intro">' + B.tx('rbKicker', 'p', 'h15-kicker')
                + f'<h1 class="h15-h2 h15-k rb-h1" id="rbTitle">{self.r("h1")}</h1>' + B.tx('rbLead', 'p', 'h15-lead') + '</div>'
                '<div class="h15-panel">' + B.tx('rbPanelKicker', 'p', 'h15-panel-kicker h15-k') + B.tx('rbPanelLabel', 'p', 'h15-panel-label h15-k')
                + f'<div class="h15-big-row"><p class="h15-big"><b>{real}</b>' + B.tx('rbUnit', cls='h15-big-unit') + B.tx('rbOf446', cls='h15-big-of')
                + f'</p><span class="h15-pct">{pct}%</span></div>'
                + f'<div aria-hidden="true" class="h15-stackbar"><i style="flex:{real} 1 0"></i><i class="is-no" style="flex:{short} 1 0"></i><i class="is-check" style="flex:{check} 1 0"></i></div>'
                '<p class="h15-legend">' + f'<span><i></i>{B.tx("rbLegendYes", cls="h15-k")}</span>'
                + f'<span><i class="is-no"></i>{B.tx("rbLegendNo", cls="h15-k")}</span>'
                + f'<span><i class="is-check"></i>{B.tx("rbLegendCheck", cls="h15-k")}</span></p></div></div>'
                + self.example() + self.areas() + '</div></section>')

    def example(self):
        B, v = self.B, self.v
        return ('<div class="h15-stack-sm">' + f'<h2 class="h15-h3 h15-k">{self.r("exTitle")}</h2>' + '<div class="h15-ex-grid">'
                '<div class="h15-card h15-ex"><div class="h15-ex-head">' + B.tx('exA', cls='h15-ex-label')
                + f'<span class="h15-verdict is-alt">{v.icon("info")}{B.tx("exAVerdict")}</span></div>'
                + B.dots(2, 4) + '<div class="h15-bts">' + B.bedtile('single', 'bedSingle', 'cnt2') + B.bedtile('sofa', 'bedSofa', 'cnt1', True)
                + B.bedtile('futon', 'bedFuton', 'cnt3f', True) + '</div></div>'
                '<div class="h15-card h15-ex"><div class="h15-ex-head">' + B.tx('exB', cls='h15-ex-label')
                + f'<span class="h15-verdict">{v.icon("check")}{B.tx("exBVerdict")}</span></div>'
                + B.dots(6) + '<div class="h15-bts">' + B.bedtile('single', 'bedSingle', 'cnt4') + B.bedtile('bunk', 'bedBunk', 'cntBunk') + '</div></div>'
                '</div>' + B.tx('exText', 'p', 'h15-note') + '</div>')

    def row(self, name, sub, part, whole, extra=''):
        p = part / whole * 100
        return (f'<div class="h15-row{extra}"><span class="h15-row-name"><span class="h15-row-area">{name}</span>'
                f'<span class="h15-row-hotels">{sub}</span></span>'
                f'<span aria-hidden="true" class="h15-bar"><i style="width:{p:.1f}%"></i></span>'
                f'<span class="h15-row-val"><b>{round(p)}%</b>' + self.B.tx('countOf', a=part, b=whole) + '</span></div>')

    def areas(self):
        B, v = self.B, self.v
        hotels, rooms, real, _, _ = self.cn['total']
        rows = [self.row(B.raw('area' + key), B.raw('hotelsN', n=h), r, rms) for key, h, rms, r in self.cn['areas']]
        rows.append('<i aria-hidden="true" class="h15-rows-sep"></i>')
        rows.append(self.row(B.raw('areaTotal'), B.raw('hotelsN', n=hotels), real, rooms, ' is-total'))
        how = [('how1', 'bed', 'howEq1', False), ('how2', 'bed', 'howEq2', False), ('how3', 'bunk', 'howEq2', False), ('how4', 'sofa', 'howSep', True)]
        lis = ''.join(('<li class="is-alt">' if alt else '<li>') + f'<span class="h15-how-name">{v.icon(ic)}{B.tx(k, cls="h15-k")}</span>'
                      + B.tx(eq, cls='h15-how-eq') + '</li>' for k, ic, eq, alt in how)
        return ('<div class="h15-two"><div class="h15-card h15-chart"><div class="h15-chart-head">'
                + B.tx('chartTitle', 'h2', 'h15-h4 h15-k') + B.tx('chartSub', cls='h15-chart-sub') + '</div><div class="h15-rows">' + ''.join(rows) + '</div></div>'
                '<div class="h15-how">' + B.tx('howTitle', 'h2', 'h15-h4') + f'<ul>{lis}</ul>' + B.tx('howNote', 'p', 'h15-note') + '</div></div>')

    def groups(self):
        hotels, rooms, real, _, _ = self.cn['total']
        rows = [self.row(self.r('gs' + g), self.r('roomsN', n=rms), k, rms, ' is-low' if g == self.n['low'] else '') for g, rms, k in self.n['groups']]
        rows.append('<i aria-hidden="true" class="h15-rows-sep"></i>')
        rows.append(self.row(self.B.raw('areaTotal'), self.r('roomsN', n=rooms), real, rooms, ' is-total'))
        return ('<div class="h15-card h15-chart rb-card"><div class="h15-chart-head">' + self.t('gsTitle', 'h2', 'h15-h4 h15-k')
                + self.t('gsSub', cls='h15-chart-sub') + '</div><div class="h15-rows">' + ''.join(rows) + '</div>'
                f'<p class="rb-callout">{self.v.icon("info")}{self.t("gsCallout")}</p></div>')

    def tile(self, kind, label, count):
        return (f'<span class="h15-bt is-alt"><svg aria-hidden="true" class="h15-bt-ill" focusable="false" viewBox="0 0 56 40"><use href="#h15-bed-{kind}"></use></svg>'
                f'<span class="h15-bt-label">{self.r(label)}</span><span class="h15-bt-count">{count}</span>{self.t("wrUnit", cls="rb-bt-unit")}</span>')

    def rest(self):
        n, top = self.n['rest'], max(c for _, c in self.n['gaps'])
        cols = ''.join(f'<div class="rb-col"><span class="rb-col-n">{c}</span><span aria-hidden="true" class="rb-col-bar"><i style="height:{c / top * 100:.1f}%"></i></span>'
                       f'{self.t("pw" + g, cls="rb-col-label")}' + self.B.dots(0, int(g), 'is-small') + '</div>' for g, c in self.n['gaps'])
        return ('<div class="rb-two"><div class="h15-card rb-card">' + self.t('wrTitle', 'h2', 'h15-h4 h15-k') + self.t('wrLead', 'p', 'h15-note')
                + '<div class="rb-tiles">' + self.tile('futon', 'wrFuton', n['futon']) + self.tile('sofa', 'wrSofa', n['sofa']) + self.tile('single', 'wrDay', n['day']) + '</div>'
                + self.t('wrNote', 'p', 'h15-note') + '</div>'
                '<div class="h15-card rb-card"><div class="h15-chart-head">' + self.t('pwTitle', 'h2', 'h15-h4 h15-k') + self.t('pwSub', cls='h15-chart-sub') + '</div>'
                f'<div class="rb-cols">{cols}</div></div></div>')

    def six(self):
        total = sum(c for _, c in self.n['six'])
        bar = ''.join(f'<i class="s{g}" style="flex:{c} 1 0"></i>' for g, c in self.n['six'])
        rows = ''.join(f'<div class="rb-six-row"><span class="rb-six-key s{g}"></span>' + self.B.dots(int(g), 6 - int(g), 'is-small')
                       + self.t('sx' + g, cls='rb-six-label') + f'<span class="rb-six-n"><b>{c}</b><span>{round(c / total * 100)}%</span></span></div>'
                       for g, c in self.n['six'])
        return ('<div class="h15-card rb-card rb-six"><div class="h15-chart-head">' + self.t('sxTitle', 'h2', 'h15-h4 h15-k') + self.t('sxSub', cls='h15-chart-sub') + '</div>'
                f'<div aria-hidden="true" class="rb-sixbar">{bar}</div><div class="rb-six-rows">{rows}</div>' + self.t('sxNote', 'p', 'h15-note') + '</div>')

    def before(self):
        items = ''.join(f'<li class="rb-check"><span class="rb-check-ic">{self.v.icon(ic)}</span>{self.t(k, "p")}</li>'
                        for ic, k in (('bed', 'bb1'), ('bath', 'bb2'), ('washer', 'bb3')))
        return '<div class="h15-stack-sm">' + self.t('bbTitle', 'h2', 'h15-h3 h15-k') + f'<ol class="rb-checks">{items}</ol></div>'

    def compare(self):
        B, v = self.B, self.v
        cards = []
        for n, r, tot in self.cn['tokyo']:
            cards.append(f'<a class="h15-card h15-tk" href="{v.esc(B.link("tokyo." + str(n)))}"><span class="h15-tk-top">'
                         + B.tx('groupOf', cls='h15-tk-label', n=n) + B.dots(n, cls='is-small') + '</span>'
                         + f'<span class="h15-tk-num"><b>{r}</b>' + B.tx('rbUnit', cls='h15-tk-unit') + B.tx('ofTotal', cls='h15-tk-of', b=tot) + '</span>'
                         + f'<span aria-hidden="true" class="h15-tk-bar"><i style="width:{r / tot * 100:.1f}%"></i></span>'
                         + '<span class="h15-tk-cta">' + B.tx('tokyoCta', n=n) + f'<span class="h15-arrow">{v.icon("arrow")}</span></span></a>')
        city = lambda href, title, sub: (f'<a class="h15-city" href="{v.esc(href)}"><span class="h15-city-text">{title}{sub}</span>'
                                         f'<span class="h15-arrow is-lime">{v.icon("arrow")}</span></a>')
        links = ''.join(city(B.link('city.' + c), B.tx('city' + c.capitalize(), 'b'), B.tx('citySub', cls='h15-k')) for c in ('osaka', 'kyoto', 'fukuoka'))
        links += city(B.link('long'), self.t('longTitle', 'b'), self.t('longSub', cls='h15-k'))
        return ('<div class="h15-stack-sm"><div class="h15-sub-head">' + self.t('compareTitle', 'h2', 'h15-h3 h15-k')
                + '<p class="h15-key"><span><b class="is-dark">' + B.tx('legBig') + '</b>' + B.tx('legBigText', cls='h15-k') + '</span>'
                + '<span><b>' + B.tx('legSmall') + '</b>' + B.tx('legSmallText', cls='h15-k') + '</span></p></div>'
                + '<div class="h15-cards3">' + ''.join(cards) + '</div>' + f'<div class="rb-links">{links}</div></div>')

    def body(self, crumb):
        return (crumb + self.v.sprite() + self.hero()
                + '<section aria-label="' + ('Results' if self.lang == 'en' else '結果') + '" class="h15 rb-more"><div class="h15-wrap h15-stack-lg">'
                + self.groups() + self.rest() + self.six() + self.before() + self.compare()
                + self.t('endNote', 'p', 'h15-note') + '</div></section>')


def build(page, art, version):
    a, b = page.find('<main>'), page.find('</main>')
    if a < 0 or b < 0 or page.count('<main>') != 1:
        raise SystemExit('<main> not found exactly once')
    crumb = re.search(r'<nav\b[^>]*\barticle-breadcrumb\b[^>]*>.*?</nav>', page[a:b], re.S)
    if not crumb:
        raise SystemExit('breadcrumb not found')
    out = page[:a + len('<main>')] + art.body(crumb.group(0)) + page[b:]
    links = ''.join(f'<link href="{h}" rel="stylesheet"/>' for h in ('/assets/gsj-home-v15.css?v=20261111', f'/assets/gsj-real-beds.css?v={version}')
                    if h.split('?')[0] not in out)
    if links:
        out = out.replace('</head>', links + '</head>', 1)
    return out


def main():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.datetime.now(jst).date().isoformat())
    ap.add_argument('--root', default=str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args()
    datetime.date.fromisoformat(a.date)
    root = Path(a.root)
    read = lambda rel: (root / rel).read_bytes().decode('utf-8')
    v = load_v15(root)
    cfg = json.loads(read('config/home-v15.json'))
    rb = json.loads(read('config/real-beds-v16.json'))
    check_numbers(cfg, rb)
    out, changed = {}, []
    for lang, rel in PAGES.items():
        old = read(rel)
        new = build(old, Article(v, cfg, rb, lang), rb['version'])
        if new != old:
            out[rel] = new
            changed.append(f'{SITE}/{lang}/real-beds/')
    xml = read('sitemap-core.xml')
    new_xml = xml
    for loc in changed:
        new_xml = v.set_lastmod(new_xml, loc, a.date)
    for rel, text in out.items():
        (root / rel).write_bytes(text.encode('utf-8'))
    if new_xml != xml:
        (root / 'sitemap-core.xml').write_bytes(new_xml.encode('utf-8'))
    print(f'pages changed: {len(changed)}' + (' (' + ', '.join(changed) + ')' if changed else '')
          + f'; sitemap-core.xml changed: {"yes" if new_xml != xml else "no"}')


if __name__ == '__main__':
    main()
