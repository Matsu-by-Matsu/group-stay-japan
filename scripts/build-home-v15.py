#!/usr/bin/env python3
"""Top page redesign (v15): builds the new sections of / (English page with its own language menu), /ko/ and /zh-tw/.

Reads config/home-v15.json (texts in en/ja/ko/zh-TW, links, numbers), config/home-stays.json and
assets/gsj-ui-translations.json (area names for the "Stays by area" list).

index.html
  - Replaces the old sections from <!-- gsj-home-beds:start --> to the end of #popularGuides (real beds table,
    "Find your group stay" with the old price table, the trust strip, the three room choices, popular group
    searches) with one block between <!-- gsj-home-v15:start --> and <!-- gsj-home-v15:end -->.
    Texts carry data-h15 keys; assets/gsj-home-v15.js switches them with the page's language menu.
  - Tags the hero line and three footer texts with data-h15, marks the Tokyo lists (#gsj-v7-tokyo),
    and replaces the Japanese middle dot "・" with "·" in the page's own Korean and Chinese texts.
  - Adds assets/gsj-home-v15.css, the text data and assets/gsj-home-v15.js.
ko/index.html, zh-tw/index.html
  - Replaces the old real-beds section and the Tokyo list with the same block, written in that language.
sitemap-core.xml
  - lastmod of the pages that changed.
Run it last, after build-home-locales.py / build-city-pages.py. Running it again changes nothing.
"""
import argparse
import datetime
import html
import json
import re
from pathlib import Path

ICONS = {
    'person': 'M8.5 7.5a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0-7 0zM5.5 20c.6-3.6 3.2-5.8 6.5-5.8s5.9 2.2 6.5 5.8',
    'check': 'M5 12.5l4.5 4.5L19 7.5',
    'info': 'M3 12a9 9 0 1 0 18 0a9 9 0 1 0-18 0zM12 11v5M12 7.5h.01',
    'bed': 'M3 7v12M3 15h18v4M21 15v-2.5A2.5 2.5 0 0 0 18.5 10H10v5M5.5 12.5h2.5',
    'bunk': 'M5 3v18M19 3v18M5 9h14M5 17h14M7.5 6.5h3M7.5 14.5h3',
    'sofa': 'M4.5 11V8.5A2.5 2.5 0 0 1 7 6h10a2.5 2.5 0 0 1 2.5 2.5V11M3 11h18v6.5H3zM5 17.5v2M19 17.5v2M7.5 14h9',
    'washer': 'M6.5 2.5h11A2.5 2.5 0 0 1 20 5v14a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 19V5a2.5 2.5 0 0 1 2.5-2.5zM7.5 13.5a4.5 4.5 0 1 0 9 0a4.5 4.5 0 1 0-9 0zM7.5 6h.01M10.5 6h3M9.6 14.1c.8-.5 1.6-.5 2.4 0s1.6.5 2.4 0',
    'kitchen': 'M4.5 10.5h15v5.5a4 4 0 0 1-4 4h-7a4 4 0 0 1-4-4v-5.5zM2.5 12.5h2M19.5 12.5h2M6 10.5c0-2.5 2.7-4.5 6-4.5s6 2 6 4.5M12 6V4',
    'arrow': 'M5 12h14M13 6l6 6-6 6',
    'home': 'M3.5 11 12 4l8.5 7M6 9.5V20h12V9.5M10 20v-5h4v5',
    'yen': 'M7 4.5l5 7 5-7M12 11.5V20M8.5 13.5h7M8.5 16.5h7',
    'shield': 'M12 3l7 2.8v5.4c0 4.5-3 7.9-7 9.3-4-1.4-7-4.8-7-9.3V5.8L12 3zM9 12l2 2 4-4',
    'moon': 'M19.5 14.2A7.5 7.5 0 0 1 9.8 4.5a7.5 7.5 0 1 0 9.7 9.7z',
    'bath': 'M3.5 12h17v2.5a5 5 0 0 1-5 5h-7a5 5 0 0 1-5-5V12zM6 12V6.5A2.5 2.5 0 0 1 10.3 5M7.5 19.5l-1 1.5M16.5 19.5l1 1.5',
}
BEDS = {
    'single': 'M6 8v26M6 20h42a2 2 0 0 1 2 2v6H6M48 28v6M9 20v-3a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v3M26 20v8',
    'sofa': 'M10 10h36a3 3 0 0 1 3 3v7H7v-7a3 3 0 0 1 3-3zM7 20v8h42v-8M4 16v12h3M52 16v12h-3M9 28v4M47 28v4M28 20v8',
    'futon': 'M3 33h50M6 23h44a2 2 0 0 1 2 2v8H4v-8a2 2 0 0 1 2-2zM8 23v-3a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v3M26 23c3 3 3 7 0 10M4 28h48',
    'bunk': 'M8 4v32M48 4v32M8 10h40M8 15h40M8 26h40M8 31h40M39 15v11M44 15v11M39 19h5M39 23h5M11 10V7.5h7V10M11 26v-2.5h7V26',
}
START, END = '<!-- gsj-home-v15:start -->', '<!-- gsj-home-v15:end -->'
SITE = 'https://groupstayjapan.synthx.jp'


def esc(v):
    return html.escape(str(v), quote=True)


def icon(name, cls='h15-i'):
    return f'<svg aria-hidden="true" class="{cls}" focusable="false" viewBox="0 0 24 24"><use href="#h15-{name}"></use></svg>'


def sprite():
    sym = ''.join(f'<symbol id="h15-{k}" viewBox="0 0 24 24"><path d="{d}"></path></symbol>' for k, d in ICONS.items())
    sym += ''.join(f'<symbol id="h15-bed-{k}" viewBox="0 0 56 40"><path d="{d}"></path></symbol>' for k, d in BEDS.items())
    return f'<svg aria-hidden="true" class="h15-sprite" focusable="false">{sym}</svg>'


class Block:
    """The three new sections in one language. dynamic=True writes data-h15 keys for the English page."""

    def __init__(self, cfg, lang, dynamic):
        self.t, self.lang, self.dyn = cfg['text'], lang, dynamic
        self.links, self.n = cfg['links'], cfg['numbers']

    def raw(self, key, **args):
        s = self.t[key][self.lang]
        for k, v in args.items():
            s = s.replace('{' + k + '}', str(v))
        return s

    def d(self, key, **args):
        if not self.dyn:
            return ''
        out = f' data-h15="{key}"'
        if args:
            out += " data-h15-args='" + json.dumps(args, separators=(',', ':')) + "'"
        return out

    def tx(self, key, tag='span', cls='', **args):
        c = f' class="{cls}"' if cls else ''
        return f'<{tag}{c}{self.d(key, **args)}>{self.raw(key, **args)}</{tag}>'

    def link(self, path):
        node = self.links
        for p in path.split('.'):
            node = node[p]
        return node[self.lang] if isinstance(node, dict) else node

    def href(self, path, suffix=''):
        out = f'href="{esc(self.link(path) + suffix)}"'
        if self.dyn:
            out += f' data-h15-href="{path}"' + (f' data-h15-suffix="{esc(suffix)}"' if suffix else '')
        return out

    @staticmethod
    def dots(real, alt=0, cls=''):
        d = ''.join(f'<span class="h15-dot">{icon("person")}</span>' for _ in range(real))
        d += ''.join(f'<span class="h15-dot is-alt">{icon("person")}</span>' for _ in range(alt))
        return f'<span aria-hidden="true" class="h15-dots{(" " + cls) if cls else ""}">{d}</span>'

    def bedtile(self, kind, label, count, alt=False):
        return (f'<span class="h15-bt{" is-alt" if alt else ""}">'
                f'<svg aria-hidden="true" class="h15-bt-ill" focusable="false" viewBox="0 0 56 40"><use href="#h15-bed-{kind}"></use></svg>'
                f'{self.tx(label, cls="h15-bt-label")}{self.tx(count, cls="h15-bt-count")}</span>')

    # ---------- A: does everyone get a real bed?
    def beds(self):
        total, rooms, real, short, check = self.n['total']
        pct = round(real / rooms * 100)
        o = ['<section aria-labelledby="h15BedsTitle" class="h15 h15-beds" id="real-beds"><div class="h15-wrap h15-stack-lg">']
        o.append('<div class="h15-beds-top"><div class="h15-beds-intro">'
                 + self.tx('rbKicker', 'p', 'h15-kicker')
                 + f'<h2 class="h15-h2 h15-k" id="h15BedsTitle"{self.d("rbTitle")}>{self.raw("rbTitle")}</h2>'
                 + self.tx('rbLead', 'p', 'h15-lead') + '</div>'
                 + '<div class="h15-panel">'
                 + self.tx('rbPanelKicker', 'p', 'h15-panel-kicker h15-k')
                 + self.tx('rbPanelLabel', 'p', 'h15-panel-label h15-k')
                 + f'<div class="h15-big-row"><p class="h15-big"><b>{real}</b>{self.tx("rbUnit", cls="h15-big-unit")}{self.tx("rbOf446", cls="h15-big-of")}</p>'
                 + f'<span class="h15-pct">{pct}%</span></div>'
                 + f'<div aria-hidden="true" class="h15-stackbar"><i style="flex:{real} 1 0"></i><i class="is-no" style="flex:{short} 1 0"></i><i class="is-check" style="flex:{check} 1 0"></i></div>'
                 + '<p class="h15-legend">'
                 + f'<span><i></i>{self.tx("rbLegendYes", cls="h15-k")}</span>'
                 + f'<span><i class="is-no"></i>{self.tx("rbLegendNo", cls="h15-k")}</span>'
                 + f'<span><i class="is-check"></i>{self.tx("rbLegendCheck", cls="h15-k")}</span></p></div></div>')
        o.append('<div class="h15-stack-sm">' + self.tx('exTitle', 'h3', 'h15-h3 h15-k') + '<div class="h15-ex-grid">'
                 + '<div class="h15-card h15-ex"><div class="h15-ex-head">' + self.tx('exA', cls='h15-ex-label')
                 + f'<span class="h15-verdict is-alt">{icon("info")}{self.tx("exAVerdict")}</span></div>'
                 + self.dots(2, 4) + '<div class="h15-bts">'
                 + self.bedtile('single', 'bedSingle', 'cnt2') + self.bedtile('sofa', 'bedSofa', 'cnt1', True)
                 + self.bedtile('futon', 'bedFuton', 'cnt3f', True) + '</div></div>'
                 + '<div class="h15-card h15-ex"><div class="h15-ex-head">' + self.tx('exB', cls='h15-ex-label')
                 + f'<span class="h15-verdict">{icon("check")}{self.tx("exBVerdict")}</span></div>'
                 + self.dots(6) + '<div class="h15-bts">'
                 + self.bedtile('single', 'bedSingle', 'cnt4') + self.bedtile('bunk', 'bedBunk', 'cntBunk') + '</div></div>'
                 + '</div>' + self.tx('exText', 'p', 'h15-note') + '</div>')
        rows = []
        for key, hotels, rms, r in self.n['areas']:
            p = r / rms * 100
            rows.append('<div class="h15-row"><span class="h15-row-name">' + self.tx('area' + key, cls='h15-row-area')
                        + self.tx('hotelsN', cls='h15-row-hotels', n=hotels) + '</span>'
                        + f'<span aria-hidden="true" class="h15-bar"><i style="width:{p:.1f}%"></i></span>'
                        + f'<span class="h15-row-val"><b>{round(p)}%</b>' + self.tx('countOf', a=r, b=rms) + '</span></div>')
        rows.append('<i aria-hidden="true" class="h15-rows-sep"></i>')
        rows.append('<div class="h15-row is-total"><span class="h15-row-name">' + self.tx('areaTotal', cls='h15-row-area')
                    + self.tx('hotelsN', cls='h15-row-hotels', n=total) + '</span>'
                    + f'<span aria-hidden="true" class="h15-bar"><i style="width:{real / rooms * 100:.2f}%"></i></span>'
                    + f'<span class="h15-row-val"><b>{pct}%</b>' + self.tx('countOf', a=real, b=rooms) + '</span></div>')
        how = [('how1', 'bed', 'howEq1', False), ('how2', 'bed', 'howEq2', False), ('how3', 'bunk', 'howEq2', False), ('how4', 'sofa', 'howSep', True)]
        lis = ''.join(('<li class="is-alt">' if alt else '<li>') + f'<span class="h15-how-name">{icon(ic)}{self.tx(k, cls="h15-k")}</span>'
                      + self.tx(eq, cls='h15-how-eq') + '</li>' for k, ic, eq, alt in how)
        o.append('<div class="h15-two"><div class="h15-card h15-chart"><div class="h15-chart-head">'
                 + self.tx('chartTitle', 'h3', 'h15-h4 h15-k') + self.tx('chartSub', cls='h15-chart-sub') + '</div><div class="h15-rows">' + ''.join(rows) + '</div></div>'
                 + '<div class="h15-how">' + self.tx('howTitle', 'h3', 'h15-h4') + f'<ul>{lis}</ul>' + self.tx('howNote', 'p', 'h15-note')
                 + f'<a class="h15-method" data-real-beds-article="" {self.href("article")}>' + self.tx('howLink', cls='h15-k')
                 + f'<span class="h15-arrow is-lime">{icon("arrow")}</span></a></div></div>')
        cards = []
        for n, r, tot in self.n['tokyo']:
            guide = f' data-home-beds-guide="{n}"' if self.dyn else ''
            cards.append(f'<a class="h15-card h15-tk"{guide} href="{esc(self.link("tokyo." + str(n)))}"><span class="h15-tk-top">'
                         + self.tx('groupOf', cls='h15-tk-label', n=n) + self.dots(n, cls='is-small') + '</span>'
                         + f'<span class="h15-tk-num"><b>{r}</b>' + self.tx('rbUnit', cls='h15-tk-unit') + self.tx('ofTotal', cls='h15-tk-of', b=tot) + '</span>'
                         + f'<span aria-hidden="true" class="h15-tk-bar"><i style="width:{r / tot * 100:.1f}%"></i></span>'
                         + '<span class="h15-tk-cta">' + self.tx('tokyoCta', n=n) + f'<span class="h15-arrow">{icon("arrow")}</span></span></a>')
        o.append('<div class="h15-stack-sm"><div class="h15-sub-head">' + self.tx('tokyoTitle', 'h3', 'h15-h3 h15-k')
                 + '<p class="h15-key"><span><b class="is-dark">' + self.tx('legBig') + '</b>' + self.tx('legBigText', cls='h15-k') + '</span>'
                 + '<span><b>' + self.tx('legSmall') + '</b>' + self.tx('legSmallText', cls='h15-k') + '</span></p></div>'
                 + '<div class="h15-cards3">' + ''.join(cards) + '</div></div>')
        cities = ''.join(f'<a class="h15-city" {self.href("city." + c)}><span class="h15-city-text">' + self.tx('city' + c.capitalize(), 'b')
                         + self.tx('citySub', cls='h15-k') + f'</span><span class="h15-arrow is-lime">{icon("arrow")}</span></a>'
                         for c in ('osaka', 'kyoto', 'fukuoka'))
        o.append('<div class="h15-stack-sm">' + self.tx('citiesTitle', 'h3', 'h15-h3 h15-k') + f'<div class="h15-cards3">{cities}</div></div>')
        o.append('</div></section>')
        return ''.join(o)

    # ---------- B: find a stay, why an apartment hotel, example calculation, trust strip
    def why(self):
        o = ['<section class="h15 h15-why-section"><div class="h15-wrap h15-stack-lg">']
        sizes = ''.join(f'<a class="h15-chip" {self.href("tokyo." + str(n))}>{icon("person")}{self.tx("g" + str(n))}</a>' for n in (4, 6, 8))
        one = '#stays' if self.dyn else f'/?lang={self.lang}#stays'
        nights = f'<a class="h15-chip" href="{esc(one)}">{icon("moon")}{self.tx("n1")}</a>'
        nights += ''.join(f'<a class="h15-chip" {self.href("long", "?nights=" + q)}>{icon("moon")}{self.tx(k)}</a>'
                          for k, q in (('n2', '2'), ('n5', '5'), ('n10', '10')))
        o.append('<div class="h15-card h15-find"><div class="h15-find-text">' + self.tx('findTitle', 'h2', 'h15-h2s h15-k')
                 + self.tx('findSub', 'p', 'h15-note h15-k') + '</div><div class="h15-find-groups">'
                 + '<div class="h15-find-group">' + self.tx('findSize', cls='h15-find-label') + f'<div class="h15-chips">{sizes}</div></div>'
                 + '<div class="h15-find-group">' + self.tx('findNights', cls='h15-find-label') + f'<div class="h15-chips">{nights}</div></div></div></div>')
        pills = ''.join(f'<span class="h15-pill">{icon(ic)}{self.tx(k)}</span>' for ic, k in (('home', 'chipUnit'), ('kitchen', 'chipKitchen'), ('washer', 'chipWasher')))
        cols = ''.join(f'<div class="h15-col"><b>{amt}</b><i style="height:{h}px"></i></div>' for amt, h in (('¥18,000', 16), ('¥72,000', 62), ('¥180,000', 156)))
        labels = ''.join(f'<span class="h15-col-label">{self.tx(k, "b")}<small>¥18,000 × {m}</small></span>' for k, m in (('night1', 1), ('night4', 4), ('night10', 10)))
        o.append('<div class="h15-why"><div class="h15-why-text">' + self.tx('whyTitle', 'h2', 'h15-h2 h15-k')
                 + self.tx('whyText', 'p', 'h15-lead is-wide') + f'<div class="h15-pills">{pills}</div></div>'
                 + '<div class="h15-card h15-calc"><div class="h15-calc-top"><div class="h15-calc-intro">'
                 + self.tx('calcKicker', 'p', 'h15-kicker') + self.tx('calcHead', 'h3', 'h15-calc-head h15-k') + '</div>'
                 + '<div class="h15-calc-group"><span class="h15-calc-group-l">' + self.dots(6, cls='is-small') + self.tx('calcGroup', cls='h15-calc-group-t') + '</span>'
                 + '<span class="h15-pct is-dark">' + self.tx('calcPct') + '</span></div>'
                 + '<div class="h15-cbs"><div class="h15-cb"><span class="h15-cb-price is-old">' + self.tx('calcPre', cls='h15-cb-pre')
                 + '<s>¥78,000</s>' + self.tx('calcUnit', cls='h15-cb-unit') + '</span>'
                 + '<span aria-hidden="true" class="h15-cb-bar"><i class="is-biz"></i></span>' + self.tx('calcBiz', cls='h15-cb-name') + '</div>'
                 + '<div class="h15-cb"><span class="h15-cb-price">' + self.tx('calcPre', cls='h15-cb-pre') + '<b>¥60,000</b>' + self.tx('calcUnit', cls='h15-cb-unit') + '</span>'
                 + '<span class="h15-cb-bar"><span class="h15-cb-save">' + self.tx('calcSave', cls='h15-cb-save-l') + '<b>¥18,000</b></span><i class="is-apt"></i></span>'
                 + self.tx('calcApt', cls='h15-cb-name is-apt') + '</div></div>'
                 + '<div class="h15-band">' + self.tx('bandSmall', cls='h15-band-small') + '<span class="h15-band-line">' + self.tx('bandPre', cls='h15-band-pre')
                 + '<span class="h15-band-num"><b>¥18,000</b>' + self.tx('bandPost', cls='h15-band-post') + '</span></span></div>'
                 + '<p class="h15-pp">' + self.tx('perPerson') + ' <s>¥13,000</s> → <b>¥10,000</b></p></div>'
                 + '<div class="h15-sum"><div class="h15-sum-head">' + self.tx('sumKicker', 'p', 'h15-kicker is-lime')
                 + self.tx('sumTitle', 'p', 'h15-sum-title h15-k') + self.tx('sumSub', 'p', 'h15-sum-sub h15-k') + '</div>'
                 + f'<div aria-hidden="true" class="h15-cols">{cols}</div><div class="h15-cols-labels">{labels}</div>'
                 + '<p class="h15-call">' + self.tx('callPre', cls='h15-k') + '<span class="h15-call-main"><b>' + self.tx('callMain') + '</b>' + self.tx('callPost', cls='h15-k') + '</span></p>'
                 + self.tx('calcNote', 'p', 'h15-sum-note') + '</div></div></div>')
        trust = ''.join(f'<li><span class="h15-trust-ico">{icon(ic)}</span>' + self.tx('trust%d' % i, cls='h15-k') + '</li>'
                        for i, ic in enumerate(('check', 'home', 'yen', 'shield'), 1))
        o.append(f'<ul class="h15-trust">{trust}</ul></div></section>')
        return ''.join(o)

    # ---------- C: three room choices and popular group searches
    def plan_connected(self):
        aria = ' data-h15-aria="figThisAria"' if self.dyn else ''
        return (f'<svg aria-label="{esc(self.raw("figThisAria"))}" class="h15-plan" role="img" viewBox="0 0 160 96"{aria}>'
                '<rect fill="#ffffff" height="90" rx="4" stroke="#164c39" stroke-width="2.5" width="154" x="3" y="3"></rect>'
                '<path d="M80 3V34M80 62V93" fill="none" stroke="#164c39" stroke-width="2.5"></path>'
                '<g fill="#e7f2eb" stroke="#164c39" stroke-width="1.2"><rect height="26" rx="2" width="16" x="10" y="10"></rect><rect height="26" rx="2" width="16" x="31" y="10"></rect>'
                '<rect height="26" rx="2" width="16" x="10" y="58"></rect><rect height="26" rx="2" width="16" x="31" y="58"></rect>'
                '<rect height="26" rx="2" width="16" x="88" y="10"></rect><rect height="26" rx="2" width="16" x="109" y="10"></rect>'
                '<rect height="26" rx="2" width="16" x="88" y="58"></rect><rect height="26" rx="2" width="16" x="109" y="58"></rect></g>'
                '<path d="M12 15h12M33 15h12M12 63h12M33 63h12M90 15h12M111 15h12M90 63h12M111 63h12" fill="none" stroke="#164c39" stroke-width="1.2"></path>'
                '<g fill="#eef1ed" stroke="#59655f" stroke-width="1.2"><rect height="18" rx="6" width="20" x="54" y="66"></rect><rect height="18" rx="6" width="20" x="132" y="66"></rect></g>'
                '<rect fill="#d8f26f" height="28" rx="4" stroke="#164c39" stroke-width="1.5" width="16" x="72" y="34"></rect>'
                '<path d="M58 48h44M63 43l-5 5 5 5M97 43l5 5-5 5" fill="none" stroke="#12392c" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2"></path></svg>')

    def plan_two(self):
        aria = ' data-h15-aria="figTwoAria"' if self.dyn else ''
        return (f'<svg aria-label="{esc(self.raw("figTwoAria"))}" class="h15-plan" role="img" viewBox="0 0 160 96"{aria}>'
                '<rect fill="#f4f5f0" height="90" width="34" x="63" y="3"></rect>'
                f'<text class="h15-plan-text" fill="#59655f" font-size="10" font-weight="700" text-anchor="middle" x="80" y="24"{self.d("figHall")}>{esc(self.raw("figHall"))}</text>'
                '<path d="M63 3H3V93H63V62M63 42V3" fill="#ffffff" stroke="#8a958f" stroke-linejoin="round" stroke-width="2.2"></path>'
                '<path d="M97 3H157V93H97V62M97 42V3" fill="#ffffff" stroke="#8a958f" stroke-linejoin="round" stroke-width="2.2"></path>'
                '<g fill="#f4f5f0" stroke="#8a958f" stroke-width="1.2"><rect height="24" rx="2" width="14" x="9" y="9"></rect><rect height="24" rx="2" width="14" x="27" y="9"></rect>'
                '<rect height="24" rx="2" width="14" x="9" y="62"></rect><rect height="24" rx="2" width="14" x="27" y="62"></rect>'
                '<rect height="24" rx="2" width="14" x="119" y="9"></rect><rect height="24" rx="2" width="14" x="137" y="9"></rect>'
                '<rect height="24" rx="2" width="14" x="119" y="62"></rect><rect height="24" rx="2" width="14" x="137" y="62"></rect></g>'
                '<g fill="#eef1ed" stroke="#8a958f" stroke-width="1.2"><rect height="18" rx="5" width="14" x="44" y="68"></rect><rect height="18" rx="5" width="14" x="102" y="68"></rect></g>'
                '<path d="M52 52H108" fill="none" stroke="#8a958f" stroke-dasharray="3 4" stroke-linecap="round" stroke-width="1.8"></path>'
                '<path d="M104 48l4 4-4 4" fill="none" stroke="#8a958f" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8"></path></svg>')

    def rooms(self):
        washer_yes = self.n['washer'][0]
        stat = lambda num, key: f'<span class="h15-stat"><b>{num}</b>{self.tx(key)}</span>'
        chip = lambda ic, key, cls='': f'<span class="h15-bchip{cls}">{icon(ic)}{self.tx(key)}</span>'
        o = ['<section aria-labelledby="h15RoomsTitle" class="h15 h15-rooms"><div class="h15-wrap h15-stack-md">',
             f'<h2 class="h15-h2 h15-k h15-narrow" id="h15RoomsTitle"{self.d("rcTitle")}>{self.raw("rcTitle")}</h2><div class="h15-rc-grid">']
        o.append('<article class="h15-card h15-rc"><div class="h15-rc-top"><div class="h15-stats">' + stat(47, 'rc1m2') + stat(6, 'rc1adults') + '</div>'
                 + self.dots(6) + '<div class="h15-bchips">' + chip('bed', 'chip4single') + chip('bunk', 'chip1bunk') + chip('bath', 'chip1bath')
                 + chip('washer', 'chipCoin', ' is-muted') + '</div></div>'
                 + '<div class="h15-rc-body">' + self.tx('rc1Title', 'h3', 'h15-h4 h15-k') + self.tx('rc1Copy', 'p')
                 + '<a class="h15-rc-link" href="https://mimaruhotels.com/en/hotel/tokyo-station-east/" rel="noopener" target="_blank">'
                 + self.tx('rcSource') + ' →</a></div></article>')
        room_guide = ' data-room-guide="eight"' if self.dyn else ''
        o.append('<article class="h15-card h15-rc"><div class="h15-rc-top"><div class="h15-stats">' + stat(82, 'rc2m2') + stat(8, 'rc2beds') + stat(2, 'rc2baths') + '</div>'
                 + '<div class="h15-figs"><figure class="h15-fig is-main">' + self.plan_connected() + '<figcaption>' + self.tx('figThis', 'b')
                 + self.tx('figThisSub', cls='h15-k') + '</figcaption></figure>'
                 + '<figure class="h15-fig">' + self.plan_two() + '<figcaption>' + self.tx('figTwo', 'b') + self.tx('figTwoSub', cls='h15-k') + '</figcaption></figure></div></div>'
                 + '<div class="h15-rc-body">' + self.tx('rc2Title', 'h3', 'h15-h4 h15-k') + self.tx('rc2Copy', 'p')
                 + f'<a class="h15-rc-link"{room_guide} href="{esc(self.link("tokyo.8"))}">' + self.tx('rc2Link') + ' →</a></div></article>')
        benefits = ''.join(f'<li><span class="h15-tick">{icon("check")}</span>' + self.tx(k, cls='h15-k') + '</li>' for k in ('washB1', 'washB2', 'washB3'))
        o.append('<article class="h15-card h15-rc"><div class="h15-rc-top is-dark">' + self.tx('washKicker', 'p', 'h15-kicker is-lime')
                 + '<div class="h15-wash"><span class="h15-wash-tile is-yes">' + icon('washer') + self.tx('washYes', cls='h15-k') + '</span>'
                 + '<span class="h15-wash-tile is-no"><svg aria-hidden="true" class="h15-i" focusable="false" viewBox="0 0 24 24"><use href="#h15-washer"></use><path d="M3 21 21 3"></path></svg>'
                 + self.tx('washNo', cls='h15-k') + '</span></div>'
                 + f'<ul class="h15-benefits">{benefits}</ul></div>'
                 + '<div class="h15-rc-body">' + self.tx('rc3Title', 'h3', 'h15-h4 h15-k') + self.tx('rc3Copy', 'p')
                 + '<div class="h15-washstat">' + self.tx('washStatLabel', cls='h15-washstat-l')
                 + f'<span class="h15-washstat-n"><b>{washer_yes}</b>' + self.tx('rbUnit', cls='h15-washstat-u') + self.tx('washOf', cls='h15-washstat-of') + '</span>'
                 + self.tx('washStatSub', cls='h15-washstat-s h15-k') + '</div>'
                 + f'<a class="h15-rc-link" {self.href("long")}>' + self.tx('washLink', cls='h15-k') + ' →</a></div></article>')
        o.append('</div>' + self.tx('rcReview', 'p', 'h15-note h15-review'))
        ids = ['seoEntryKicker', 'seoEntryTitle', 'seoEntryCopy', 'seoGuideLinks'] if self.dyn else [None] * 4
        idattr = lambda i: f' id="{i}"' if i else ''
        tiles = ''.join(self.guide_tile(i) for i in range(4))
        o.append('<div class="h15-guides"' + idattr('popularGuides' if self.dyn else None) + '><div class="h15-guides-text">'
                 + f'<p class="h15-kicker is-lime"{idattr(ids[0])}{self.d("guKicker")}>{self.raw("guKicker")}</p>'
                 + f'<h2 class="h15-h2s is-white h15-k"{idattr(ids[1])}{self.d("guTitle")}>{self.raw("guTitle")}</h2>'
                 + f'<p class="h15-guides-copy"{idattr(ids[2])}{self.d("guCopy")}>{self.raw("guCopy")}</p></div>'
                 + f'<div class="h15-gts"{idattr(ids[3])}>{tiles}</div></div>')
        o.append('</div></section>')
        return ''.join(o)

    def guide_tile(self, i):
        href = self.links['guides'][self.lang][i]
        if i < 3:
            ico = self.dots((4, 6, 8)[i], cls='is-small is-dark')
        else:
            ico = f'<span aria-hidden="true" class="h15-gt-icons">{icon("kitchen")}{icon("washer")}</span>'
        # same click event as the page's own updateSeoEntry() (item_id is the link's full URL)
        ga = ' onclick="gaEvent(\'select_content\',{content_type:\'seo_guide\',item_id:href})"' if self.dyn else ''
        return (f'<a class="h15-gt" href="{esc(href)}"{ga}>{ico}<span class="h15-gt-row">'
                f'<b class="h15-k">{self.raw("gu%d" % i)}</b><span class="h15-arrow is-dark">{icon("arrow")}</span></span></a>')

    def block(self):
        return START + sprite() + self.beds() + self.why() + self.rooms() + END


def runtime_data(cfg, stays, ui):
    """Everything assets/gsj-home-v15.js needs on the English page."""
    text = {lang: {k: v[lang] for k, v in cfg['text'].items()} for lang in ('en', 'ja', 'ko', 'zh-TW')}
    areas = {}
    for s in stays['stays']:
        a = s['area_en']
        areas.setdefault(a, {'ja': ui['areas'].get(a, a), 'ko': s['area_ko'], 'zh-TW': s['area_zh']})
    return {'text': text, 'places': cfg['places'], 'areas': areas, 'links': cfg['links']}


def section_end(s, start):
    """Index just after the </section> that closes the <section ...> opening at `start` (nested sections allowed)."""
    depth = 0
    for m in re.compile(r'<section\b|</section>').finditer(s, start):
        depth += 1 if m.group(0) == '<section' else -1
        if depth == 0:
            return m.end()
    raise SystemExit('unclosed <section>')


def replace_block(s, new, old_start, old_end):
    if START in s:
        a = s.index(START)
        b = s.index(END, a) + len(END)
    else:
        if s.count(old_start) != 1:
            raise SystemExit(f'expected exactly one {old_start!r}')
        a = s.index(old_start)
        b = old_end(s, a)
    return s[:a] + new + s[b:]


def end_of_popular_guides(s, a):
    return section_end(s, s.index('<section class="seo-entry" id="popularGuides">', a))


def dict_dots(s):
    """'・' -> '·' inside the page's own Korean and Chinese dictionaries and in the Tokyo list heading."""
    for name in ('zh', 'ko'):
        a = s.index('const %s={' % name)
        i, depth = a + len('const %s=' % name), 0
        while True:
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        s = s[:a] + s[a:i].replace('・', '·') + s[i:]
    return s.replace("'zh-TW':['東京・依人數'", "'zh-TW':['東京·依人數'")


def put_css(s, href):
    tag = f'<link href="{href}" rel="stylesheet"/>'
    s = re.sub(r'<link href="/assets/gsj-home-v15\.css\?v=[^"]*" rel="stylesheet"/>', lambda m: tag, s)
    return s if tag in s else s.replace('</head>', tag + '</head>', 1)


def build_en(s, cfg, stays, ui):
    s = replace_block(s, Block(cfg, 'en', True).block(), '<!-- gsj-home-beds:start -->', end_of_popular_guides)
    # an old generator (scripts/build_v31.py) puts "Find your group stay" back above; the new block already has it
    while '<section class="gsj-v31 gsj-wrap">' in s:
        a = s.index('<section class="gsj-v31 gsj-wrap">')
        s = s[:a] + s[section_end(s, a):]
    s = put_css(s, cfg['css'])
    data = json.dumps(runtime_data(cfg, stays, ui), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    tail = f'<script id="gsj-h15-data" type="application/json">{data}</script><script defer="" src="{cfg["js"]}"></script>'
    s = re.sub(r'<script id="gsj-h15-data" type="application/json">.*?</script><script defer="" src="/assets/gsj-home-v15\.js\?v=[^"]*"></script>',
               lambda m: tail, s, flags=re.S)
    if tail not in s:
        s = s.replace('</body>', tail + '</body>', 1)
    for old, new in [
        ('<p class="lead">Stay together. Stay longer.</p>', '<p class="lead" data-h15="heroLead">Stay together. Stay longer.</p>'),
        ('<a href="_SYSTEM/about.html">About GROUP STAY JAPAN</a>', '<a data-h15="footAbout" href="_SYSTEM/about.html">About GROUP STAY JAPAN</a>'),
        ('<div class="copyright">© 2026 GROUP STAY JAPAN. All rights reserved.<br/><span style="opacity:.75">',
         '<div class="copyright"><span data-h15="footCopy">© 2026 GROUP STAY JAPAN. All rights reserved.</span><br/><span data-h15="footAffiliate" style="opacity:.75">'),
        ('<section class="gsj-wrap" id="gsj-v7-tokyo">', '<section class="gsj-wrap" data-h15-langlists="" id="gsj-v7-tokyo">'),
    ]:
        if old in s:
            s = s.replace(old, new, 1)
        elif new not in s:
            raise SystemExit('index.html: not found: ' + old)
    return dict_dots(s)


def build_locale(s, cfg, lang):
    end = lambda t, a: t.index('<section class="guide" id="regional-stays">', a)
    s = replace_block(s, Block(cfg, lang, False).block(), '<section class="guide">', end)
    return put_css(s, cfg['css'])


def set_lastmod(xml, loc, day):
    pat = re.compile(r'(<loc>' + re.escape(loc) + r'</loc>\s*<lastmod>)[^<]*(</lastmod>)')
    if not pat.search(xml):
        raise SystemExit('sitemap-core.xml: no lastmod for ' + loc)
    return pat.sub(lambda m: m.group(1) + day + m.group(2), xml)


def main():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.datetime.now(jst).date().isoformat())
    ap.add_argument('--root', default=str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args()
    datetime.date.fromisoformat(a.date)
    root = Path(a.root)
    read = lambda rel: (root / rel).read_bytes().decode('utf-8')  # bytes in, bytes out: line endings stay as they are
    cfg = json.loads(read('config/home-v15.json'))
    stays = json.loads(read('config/home-stays.json'))
    ui = json.loads(read('assets/gsj-ui-translations.json'))
    jobs = [('index.html', lambda s: build_en(s, cfg, stays, ui), SITE + '/'),
            ('ko/index.html', lambda s: build_locale(s, cfg, 'ko'), SITE + '/ko/'),
            ('zh-tw/index.html', lambda s: build_locale(s, cfg, 'zh-TW'), SITE + '/zh-tw/')]
    changed = []
    for rel, fn, loc in jobs:
        old = read(rel)
        new = fn(old)
        if new != old:
            (root / rel).write_bytes(new.encode('utf-8'))
            changed.append(loc)
    xml = read('sitemap-core.xml')
    new_xml = xml
    for loc in changed:
        new_xml = set_lastmod(new_xml, loc, a.date)
    if new_xml != xml:
        (root / 'sitemap-core.xml').write_bytes(new_xml.encode('utf-8'))
    print(f'pages changed: {len(changed)}' + (' (' + ', '.join(changed) + ')' if changed else '')
          + f'; sitemap-core.xml changed: {"yes" if new_xml != xml else "no"}')


if __name__ == '__main__':
    main()
