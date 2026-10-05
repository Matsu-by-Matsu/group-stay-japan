"""Add home-page bed facts without regenerating any existing page.
Run with --date YYYY-MM-DD. All input validation precedes output writes.
"""
import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TEXTS = {'realBedsTitle': ['Does everyone get a real bed?', '全員がベッドで寝られるか', '每個人都有床可睡嗎？', '모두 침대에서 잘 수 있을까요?'], 'realBedsLead': ['A room that sleeps six does not always have six beds. We counted the beds in all {rooms} room types at the {hotels} hotels we compare, using each hotel’s official room details.', '定員6人の部屋に、ベッドが6人分あるとは限りません。比較している{hotels}施設・{rooms}室の寝具を、各施設の公式の客室情報からすべて数えました。', '可住6人的房間，不一定有6人份的床。我們依各飯店的官方客房資訊，逐一計算了所比較的{hotels}間飯店、全部{rooms}種房型的床位。', '정원이 6명인 객실이라도 침대가 6명분 있는 것은 아닙니다. 비교하는 {hotels}개 호텔의 {rooms}개 객실 유형을 각 호텔의 공식 객실 정보로 모두 세었습니다.'], 'realBedsTotal': ['<strong>{all} of the {rooms}</strong> room types give every guest a real bed at full capacity. {check} need checking on the official site.', '定員いっぱいでも全員がベッドで寝られる客室は<strong>{rooms}室中{all}室</strong>。{check}室は公式サイトで確認が必要です。', '滿房時全員都有床可睡的房型：<strong>{rooms}種中{all}種</strong>。{check}種需至官方網站確認。', '정원이 다 차도 모두 침대에서 잘 수 있는 객실: <strong>{rooms}개 중 {all}개</strong>. {check}개는 공식 사이트에서 확인이 필요합니다.'], 'realBedsArea': ['Area', '地域', '地區', '지역'], 'realBedsHotels': ['Hotels', '施設', '飯店', '호텔'], 'realBedsRooms': ['Room types', '客室', '房型', '객실 유형'], 'realBedsAll': ['Every guest in a real bed at full capacity', '定員いっぱいでも全員がベッドで寝られる客室', '滿房時全員都有床可睡的房型', '정원이 다 차도 모두 침대에서 잘 수 있는 객실'], 'realBedsAreaTokyo': ['Tokyo', '東京', '東京', '도쿄'], 'realBedsAreaKyoto': ['Kyoto', '京都', '京都', '교토'], 'realBedsAreaOsaka': ['Osaka', '大阪', '大阪', '오사카'], 'realBedsAreaHokkaido': ['Hokkaido', '北海道', '北海道', '홋카이도'], 'realBedsAreaFukuoka': ['Fukuoka', '福岡', '福岡', '후쿠오카'], 'realBedsAreaOther': ['Other areas', 'その他の地域', '其他地區', '기타 지역'], 'realBedsAreaTotal': ['All areas', '全体', '全部', '전체'], 'realBedsTokyo': ['Tokyo, by group size', '東京・人数別', '東京・依人數', '도쿄 · 인원별'], 'realBeds4': ['4 guests: {n4} of {m4} room types give all 4 a real bed →', '4人：{m4}室のうち、4人全員がベッドで寝られるのは{n4}室 →', '4人：{m4}種房型中，4人全都有床可睡的有{n4}種 →', '4명: {m4}개 객실 중 4명 모두 침대에서 잘 수 있는 객실은 {n4}개 →'], 'realBeds6': ['6 guests: {n6} of {m6} room types give all 6 a real bed →', '6人：{m6}室のうち、6人全員がベッドで寝られるのは{n6}室 →', '6人：{m6}種房型中，6人全都有床可睡的有{n6}種 →', '6명: {m6}개 객실 중 6명 모두 침대에서 잘 수 있는 객실은 {n6}개 →'], 'realBeds8': ['8 guests: {n8} of {m8} room types give all 8 a real bed →', '8人：{m8}室のうち、8人全員がベッドで寝られるのは{n8}室 →', '8人：{m8}種房型中，8人全都有床可睡的有{n8}種 →', '8명: {m8}개 객실 중 8명 모두 침대에서 잘 수 있는 객실은 {n8}개 →'], 'realBedsExample': ['Example: one room type for 6 has 2 single beds, 1 sofa bed and 3 futons, so only 2 of the 6 sleep in a real bed. Another has 4 single beds and 1 bunk bed, so all 6 do.', '例：定員6人のある客室は、シングルベッド2台・ソファベッド1台・布団3組で、ベッドで寝られるのは6人中2人です。定員6人の別の客室は、シングルベッド4台と二段ベッド1台で、6人全員がベッドで寝られます。', '例如：某個可住6人的房型有2張單人床、1張沙發床和3組日式床墊，6人中只有2人有床可睡。另一個可住6人的房型有4張單人床和1組上下舖，6人全都有床可睡。', '예: 정원 6명인 한 객실은 싱글 침대 2개, 소파베드 1개, 요이불 3개로, 6명 중 2명만 침대에서 잘 수 있습니다. 정원 6명인 다른 객실은 싱글 침대 4개와 2층 침대 1개로, 6명 모두 침대에서 잘 수 있습니다.'], 'realBedsNote': ['How we count: single, semi-double and loft beds = 1 person; double, queen and king beds = 2; each bunk bed = 2. Sofa beds, day beds and futons are counted separately. Bed details from the official sites (checked 2026-09-25).', '数え方：シングル・セミダブル・ロフトベッドは1人、ダブル・クイーン・キングは2人、二段ベッドは1台2人。ソファベッド・デイベッド・布団は別に数えています。寝具は公式サイトの記載（2026/9/25確認）。', '計算方式：單人床、小雙人床、閣樓床各算1人；雙人床、加大雙人床、特大雙人床各算2人；上下舖每組算2人。沙發床、坐臥兩用床、日式床墊另計。床型依官方網站（2026/9/25確認）。', '계산 방법: 싱글·세미더블·로프트 침대는 1명, 더블·퀸·킹 침대는 2명, 2층 침대는 1대에 2명. 소파베드·데이베드·요이불은 따로 셉니다. 침대 구성은 공식 사이트 기준(2026/9/25 확인).']}
OLD_DESC = 'Apartment hotels for groups and longer stays in Japan. Compare official room capacities, kitchens, laundry and cleaning policies.'
CSS = '<link href="/assets/gsj-home-beds.css?v=20261005" rel="stylesheet"/>'
JS = '<script defer src="/assets/gsj-home-beds.js?v=20261005"></script>'
AREAS = ['tokyo', 'kyoto', 'osaka', 'hokkaido', 'fukuoka', 'other']

def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()

def write(p, text):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

def require(test, message):
    if not test:
        raise ValueError(message)

def clean(text):
    text = re.sub(r'<!-- gsj-home-beds:start -->.*?<!-- gsj-home-beds:end -->', '', text, flags=re.S)
    text = re.sub(r'/\* gsj-home-beds:start \*/.*?/\* gsj-home-beds:end \*/', '', text, flags=re.S)
    return text.replace(CSS, '').replace(JS, '')

def state(room):
    if room['status'] == 'ambiguous':
        return 'check'
    b, o, cap = room['bedSleepers'], room['otherSleepers'], room['capacity']
    return 'all' if b >= cap else 'partial' if b + o >= cap else 'gap'

def catalog(html):
    match = re.search(r'const stays=\[(.*?)\];', html, re.S)
    require(match is not None, 'Cannot find stays array')
    base = []
    for item in re.findall(r'\{[^{}]+\}', match[1]):
        slug = re.search(r"\bid:'([^']+)'", item)
        city = re.search(r"\bcity:'([^']+)'", item)
        maximum = re.search(r'\bmax:(\d+)', item)
        require(slug and city and maximum, 'Cannot parse stay id/city/max')
        base.append({'id': slug[1], 'city': city[1], 'max': int(maximum[1])})
    extra = read(ROOT / '_SYSTEM/catalog.js')
    extra = json.JSONDecoder().raw_decode(extra.split('window.GSJ_EXTRA_STAYS=', 1)[1])[0]
    out = {s['id']: s for s in base}
    for s in extra:
        if s['id'] not in out:
            out[s['id']] = s
    return out

def build(day):
    original = read(ROOT / 'index.html')
    html = clean(original)
    all_data = json.loads(read(ROOT / 'config/bed-sleepers.json'))['properties']
    excluded = set(json.loads(read(ROOT / 'config/stay-rules.json'))['excludedProperties'])
    data = {k: v for k, v in all_data.items() if k not in excluded}
    cat = {k: v for k, v in catalog(html).items() if k not in excluded}
    require(len(data) == 78 and set(cat) == set(data), 'Expected matching 78 property keys')
    rows = [room for rooms in data.values() for room in rooms]
    counts = Counter(state(room) for room in rows)
    numbers = {'hotels': len(data), 'rooms': len(rows), 'all': counts['all'], 'check': counts['check']}
    new_desc = f'Apartment hotels for groups and longer stays in Japan. See how many of {len(rows)} room types give every guest a real bed, and compare kitchens and laundry.'
    markers = ['<section class="gsj-v31 gsj-wrap">', '</head>', 'const pageParams=new URLSearchParams(location.search);', '<script defer="True" src="/assets/gsj-readiness.js?v=20260926"></script>']
    for marker in markers:
        require(html.count(marker) == 1, 'Expected exactly one marker: ' + marker)
    desc_old = f'<meta content="{OLD_DESC}" name="description"/>'
    desc_new = f'<meta content="{new_desc}" name="description"/>'
    require(sum(html.count(s) for s in [desc_old, desc_new]) == 1, 'Description marker missing or duplicated')
    for slug, room_id, capacity, beds, sleepers in [
        ('minn-nihonbashi', 'room-0', 6, 'シングルベッド×2、ソファベッド×1、布団×3', 2),
        ('mimaru-tokyo-station-east', 'room-8', 6, 'シングルベッド×4、二段ベッド×1', 6)]:
        room = next(r for r in data[slug] if r['id'] == room_id)
        require((room['capacity'], room['bedsJa'], room['bedSleepers']) == (capacity, beds, sleepers), 'Example changed: ' + slug)
    areas = {area: [0, 0, 0] for area in AREAS}
    compact = {}
    for slug, rooms in data.items():
        city = cat[slug].get('city')
        require(isinstance(city, str) and bool(city), 'Unknown city: ' + slug)
        area = city if city in AREAS[:-1] else 'other'
        areas[area][0] += 1
        areas[area][1] += len(rooms)
        areas[area][2] += sum(state(r) == 'all' for r in rooms)
        eligible = [r for r in rooms if not (slug == 'mimaru-ueno-inaricho' and r['id'] == 'room-2')]
        compact[slug] = [[r['capacity'], None if r['status'] == 'ambiguous' else r['bedSleepers']] for r in eligible]
        for q in range(2, 13):
            if cat[slug]['max'] >= q and not any(r['capacity'] >= q for r in eligible):
                require(slug == 'mimaru-ueno-inaricho' and q >= 5, 'Unexpected bundle-only property: ' + slug)
    require([sum(a[i] for a in areas.values()) for i in range(3)] == [numbers['hotels'], numbers['rooms'], numbers['all']], 'Area total mismatch')
    for n in [4, 6, 8]:
        soup = BeautifulSoup(read(ROOT / f'en/tokyo/hotels-for-{n}-guests/index.html'), 'html.parser')
        table = soup.select('.gsj-readiness-table tr[data-property]')
        expected = {(slug, r['id']): r for slug, rr in data.items() if cat[slug]['city'] == 'tokyo' for r in rr if r['capacity'] >= n and not (slug == 'mimaru-ueno-inaricho' and r['id'] == 'room-2')}
        found = set()
        for row in table:
            href = row.find_all('td')[0].a['href']
            key = (row['data-property'], 'room-' + parse_qs(urlsplit(href).query)['room'][0])
            require(key in expected and key not in found, 'Guide room mismatch or duplicate')
            found.add(key)
            room = expected[key]
            val = 'check' if room['status'] == 'ambiguous' else '1' if room['bedSleepers'] >= n else '0'
            require(row.get('data-all-beds') == val, 'Guide bed flag mismatch')
        require(found == set(expected), 'Guide room cohort mismatch')
        numbers[f'm{n}'] = len(table)
        numbers[f'n{n}'] = sum(row['data-all-beds'] == '1' for row in table)
    t = {key: [value.format(**numbers) for value in values] for key, values in TEXTS.items()}
    def tag(name, key, cls=None, id_=None):
        attrs = (f' class="{cls}"' if cls else '') + f' data-i18n="{key}"' + (f' id="{id_}"' if id_ else '')
        return f'<{name}{attrs}>{t[key][0]}</{name}>'
    section = '<!-- gsj-home-beds:start --><section aria-labelledby="realBedsTitle" class="gsj-home-beds" id="real-beds"><div class="container">'
    section += tag('h2', 'realBedsTitle', id_='realBedsTitle') + tag('p', 'realBedsLead', 'gsj-home-beds-lead') + tag('p', 'realBedsTotal', 'gsj-home-beds-total')
    section += '<div class="gsj-home-beds-table"><table><thead><tr>'
    section += ''.join(f'<th data-i18n="{k}" scope="col">{t[k][0]}</th>' for k in ['realBedsArea', 'realBedsHotels', 'realBedsRooms', 'realBedsAll']) + '</tr></thead><tbody>'
    for area, (hotels, rooms, all_) in list(areas.items()) + [('total', [numbers['hotels'], numbers['rooms'], numbers['all']])]:
        key = 'realBedsArea' + area.title()
        section += ('<tr class="gsj-home-beds-sum">' if area == 'total' else '<tr>') + f'<th data-i18n="{key}" scope="row">{t[key][0]}</th><td>{hotels}</td><td>{rooms}</td><td>{all_} ({int(all_ / rooms * 100 + .5)}%)</td></tr>'
    section += '</tbody></table></div>' + tag('h3', 'realBedsTokyo') + '<ul class="gsj-home-beds-links">'
    for n in [4, 6, 8]:
        section += f'<li><a data-home-beds-guide="{n}" data-i18n="realBeds{n}" href="/en/tokyo/hotels-for-{n}-guests/">{t[f"realBeds{n}"][0]}</a></li>'
    section += '</ul>' + tag('p', 'realBedsExample', 'gsj-home-beds-example') + tag('p', 'realBedsNote', 'gsj-home-beds-note') + '</div></section><!-- gsj-home-beds:end -->'
    translations = '/* gsj-home-beds:start */'
    for i, lang in enumerate(['ja', 'zh', 'ko'], 1):
        translations += 'Object.assign(' + lang + ',{' + ','.join(k + ':' + json.dumps(v[i], ensure_ascii=False) for k, v in t.items()) + '});'
    translations += '/* gsj-home-beds:end */'
    html = html.replace(markers[0], section + markers[0]).replace(markers[1], CSS + markers[1]).replace(markers[2], translations + markers[2]).replace(markers[3], markers[3] + JS).replace(desc_old, desc_new)
    require(clean(html).replace(desc_new, desc_old) == clean(original).replace(desc_new, desc_old), 'Existing content changed')
    xml = read(ROOT / 'sitemap-core.xml')
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    tree = ET.fromstring(xml)
    require(len(tree.findall('s:url', ns)) == 19, 'Expected 19 sitemap URLs')
    root_entries = re.findall(r'<url>\s*<loc>https://groupstayjapan\.synthx\.jp/</loc>.*?</url>', xml, re.S)
    require(len(root_entries) == 1, 'Expected one root sitemap entry')
    entry, num = re.subn(r'<lastmod>[^<]+</lastmod>', f'<lastmod>{day}</lastmod>', root_entries[0])
    require(num == 1, 'Expected one root lastmod')
    xml = xml.replace(root_entries[0], entry)
    ET.fromstring(xml)
    outputs = {'index.html': html, 'sitemap-core.xml': xml, 'assets/gsj-home-beds.json': json.dumps({'properties': compact}, ensure_ascii=False, separators=(',', ':')) + '\n'}
    for path, content in outputs.items():
        write(ROOT / path, content)
    return {'date': day, 'counts': numbers, 'states': dict(counts), 'areas': areas, 'cardProperties': len(compact), 'cardRooms': sum(map(len, compact.values())), 'cardNulls': sum(r[1] is None for rr in compact.values() for r in rr)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default=datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d'))
    args = parser.parse_args()
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
        print(json.dumps(build(args.date), ensure_ascii=True, indent=2))
    except (ValueError, KeyError, IndexError, StopIteration, TypeError, ET.ParseError) as exc:
        print('Validation failed: ' + str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
