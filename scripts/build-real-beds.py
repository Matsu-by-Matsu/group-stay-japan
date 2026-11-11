"""Build v9 static real-bed articles and narrowly add their incoming links.
Run --date YYYY-MM-DD for the intended publication day. Validate all totals
before writing any HTML. Existing files retain their byte format outside edits.
"""
import argparse, copy, importlib.util, json, re, sys
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone, timedelta
from html import escape
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE = "https://groupstayjapan.synthx.jp"
DEFAULT_INPUT = ROOT.parent / "gsj-phase1-20260925/bed-sleepers-20261003.json"
COPY = {'en': {'title': 'Does Everyone Get a Real Bed? 446 Apartment-Hotel Rooms in Japan | GROUP STAY JAPAN', 'description': 'We counted the beds in 446 apartment-hotel room types in Japan. Only 259 give every guest a real bed at full capacity. Results by area and group size.', 'h1': 'Does everyone get a real bed?', 'lead': "A room for six does not always have six beds. We counted the beds in all 446 room types at the 78 apartment hotels we compare, using each hotel's official room details.", 'result': '259 of the 446 room types (58%) give every guest a real bed at full capacity. 5 need checking on the official site.', 'note': "Bed details can change. Always confirm on the hotel's official site before booking.", 'sections': [{'heading': 'How we counted', 'lines': ['Single, semi-double and loft beds: 1 person each.', 'Double, queen and king beds: 2 people each.', 'Bunk beds: 2 people each.', 'Sofa beds, day beds and futons are counted separately, not as beds.', "Source: each hotel's official room details, checked on 25 September 2026. Five room types describe their bunk beds in a way we could not count, so we left them out."]}, {'heading': 'By area', 'lines': ['列：Area / Hotels / Room types / Every guest in a real bed at full capacity', '行：Tokyo 26 / 146 / 86 (59%)、Kyoto 14 / 103 / 35 (34%)、Osaka 9 / 53 / 27 (51%)、Hokkaido 3 / 21 / 15 (71%)、Fukuoka 5 / 19 / 16 (84%)、Other areas 21 / 104 / 80 (77%)、All areas 78 / 446 / 259 (58%)']}, {'heading': 'By group size', 'lines': ['列：Room capacity / Room types / Every guest in a real bed at full capacity', '行：2–3 guests 36 / 18 (50%)、4 guests 196 / 138 (70%)、5 guests 55 / 12 (22%)、6 guests 113 / 67 (59%)、7 guests 9 / 3 (33%)、8 or more guests 37 / 21 (57%)、All 446 / 259 (58%)', '表の下：Rooms for five are the hardest: only 12 of 55 give all five guests a real bed.']}, {'heading': 'Where the rest of the group sleeps', 'lines': ["In 182 room types, the beds hold fewer people than the room's capacity. The rest of the group sleeps on futons (in 104 of these room types), sofa beds (79) or day beds (14). Some rooms use more than one.", '表（列：People without a real bed / Room types）：1 / 42、2 / 91、3 / 32、4 or more / 17']}, {'heading': 'Rooms for six', 'lines': ['Of the 113 room types for six guests, 67 have real beds for all six. 37 have beds for four, 1 has beds for three, and 8 have beds for only two.']}, {'heading': 'Before you book', 'lines': ['Check the bed types and counts, and whether sofa beds or futons are part of the capacity.', 'Check how many bathrooms there are.', 'For longer stays, check whether the washing machine is in the room or shared.']}, {'heading': 'Compare stays in Tokyo', 'lines': ['リンク：4 guests → /en/tokyo/hotels-for-4-guests/、6 guests → /en/tokyo/hotels-for-6-guests/、8 guests → /en/tokyo/hotels-for-8-guests/、Longer stays → /en/tokyo/apartment-hotels-for-longer-stays/']}]}, 'ja': {'title': '全員がベッドで寝られる？ アパートメントホテル446室のベッドを数えた結果 | GROUP STAY JAPAN', 'description': '日本のアパートメントホテル446の部屋タイプのベッドを数えました。定員いっぱいで全員がベッドで寝られるのは259。地域別・人数別の結果です。', 'h1': '全員がベッドで寝られる？', 'lead': '6人で泊まれる部屋に、ベッドが6人分あるとは限りません。GROUP STAY JAPANで比べている78のアパートメントホテル、446の部屋タイプすべてについて、各ホテルの公式の客室情報からベッドを数えました。', 'result': '定員いっぱいで全員がベッドで寝られるのは、446のうち259（58%）でした。5つは公式サイトでの確認が必要です。', 'note': 'ベッドの情報は変わることがあります。予約の前に、必ずホテルの公式サイトで確かめてください。', 'sections': [{'heading': '数え方', 'lines': ['シングル・セミダブル・ロフトベッド：1台1人', 'ダブル・クイーン・キング：1台2人', '二段ベッド：1台2人', 'ソファベッド・デイベッド・布団は、ベッドに数えず別に数えます。', '出典：各ホテルの公式の客室情報（2026年9月25日に確認）。二段ベッドの書き方から人数を数えられなかった5つの部屋タイプは除いています。']}, {'heading': '地域別', 'lines': ['列：地域 / ホテル数 / 部屋タイプ数 / 定員いっぱいで全員がベッドで寝られる']}, {'heading': '人数別', 'lines': ['列：定員 / 部屋タイプ数 / 定員いっぱいで全員がベッドで寝られる', '表の下：5人用の部屋がいちばん少なく、55のうち12でした。']}, {'heading': 'ベッドが足りない分は', 'lines': ['ベッドで寝られる人数が定員より少ない部屋タイプは182ありました。残りの人は、布団（182のうち104）、ソファベッド（79）、デイベッド（14）で寝ます。1つの部屋で2種類以上のこともあります。', '表（列：ベッドで寝られない人数 / 部屋タイプ数）：1人 / 42、2人 / 91、3人 / 32、4人以上 / 17']}, {'heading': '6人用の部屋', 'lines': ['6人用の113の部屋タイプのうち、6人全員がベッドで寝られるのは67でした。ベッドが4人分のものが37、3人分が1、2人分だけのものが8でした。']}, {'heading': '予約の前に確かめること', 'lines': ['ベッドの種類と数。ソファベッドや布団が定員に入っているか', 'バスルームの数', '長期滞在なら、洗濯機が部屋の中にあるか、共用か']}, {'heading': '東京で比べる', 'lines': ['リンク：4人 → /ja/tokyo/4-guests/、6人 → /ja/tokyo/6-guests/、8人 → /ja/tokyo/8-guests/、長期滞在 → /ja/tokyo/long-stay-apartment-hotels/']}]}}

def read(path):
    return path.read_bytes().decode('utf-8')

def require(condition, message):
    if not condition:
        raise ValueError(message)

def aggregate(input_path, home):
    data = json.loads(read(input_path))['properties']
    excluded = set(json.loads(read(ROOT / 'config/stay-rules.json'))['excludedProperties'])
    require(all(not data[k] for k in excluded), 'Excluded properties unexpectedly have rooms')
    data = {k: v for k, v in data.items() if k not in excluded}
    spec = importlib.util.spec_from_file_location('home_beds', ROOT / 'scripts/add-home-beds.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    catalog = module.catalog(home)
    rows = [r for rooms in data.values() for r in rooms]
    full = lambda r: r['status'] == 'ok' and r['bedSleepers'] >= r['capacity']
    area_keys = ['tokyo', 'kyoto', 'osaka', 'hokkaido', 'fukuoka', 'other']
    area_rows = []
    for area in area_keys:
        ids = [k for k in data if (catalog[k]['city'] if catalog[k]['city'] in area_keys[:-1] else 'other') == area]
        rooms = [r for k in ids for r in data[k]]
        area_rows.append([len(ids), len(rooms), sum(map(full, rooms))])
    totals = [len(data), len(rows), sum(map(full, rows))]
    check = sum(r['status'] != 'ok' for r in rows)
    bucket = lambda r: 3 if r['capacity'] <= 3 else min(8, r['capacity'])
    groups = [[sum(bucket(r) == n for r in rows), sum(full(r) for r in rows if bucket(r) == n)] for n in [3, 4, 5, 6, 7, 8]]
    short = [r for r in rows if r['status'] == 'ok' and r['bedSleepers'] < r['capacity']]
    other = [sum(word in r['bedsJa'] for r in short) for word in ['布団', 'ソファベッド', 'デイベッド']]
    gaps = [sum(min(4, r['capacity'] - r['bedSleepers']) == n for r in short) for n in [1, 2, 3, 4]]
    six = dict(sorted(Counter(r['bedSleepers'] for r in rows if r['capacity'] == 6).items()))
    expected = [[26,146,86],[14,103,35],[9,53,27],[3,21,15],[5,19,16],[21,104,80]]
    require(area_rows == expected, f'Area mismatch: {area_rows}')
    require(totals == [78,446,259] and check == 5, f'Totals mismatch: {totals}, {check}')
    require(groups == [[36,18],[196,138],[55,12],[113,67],[9,3],[37,21]], f'Group mismatch: {groups}')
    require(len(short) == 182 and other == [104,79,14] and gaps == [42,91,32,17], f'Shortfall mismatch: {len(short)}, {other}, {gaps}')
    require(six == {2:8,3:1,4:37,6:67}, f'Six-person mismatch: {six}')
    soup = BeautifulSoup(home, 'html.parser')
    note = soup.select_one('[data-i18n="realBedsNote"]')
    table = note.find_parent('section').find('table')
    actual = [[td.get_text(strip=True) for td in tr.find_all('td')] for tr in table.select('tr') if tr.find('td')]
    require(len(actual) == 7, 'Home table row count differs')
    for row, nums in zip(actual, area_rows + [totals]):
        require(row[-3:] == [str(nums[0]), str(nums[1]), pct(nums[2],nums[1])], f'Home table mismatch: {row}')
    report = {'areas':dict(zip(area_keys,area_rows)), 'totals':totals, 'needsChecking':check, 'capacityGroups':dict(zip(['2-3','4','5','6','7','8+'],groups)), 'shortfallRooms':len(short), 'futonsSofasDayBeds':other, 'shortfallPeople1_2_3_4plus':gaps, 'sixPersonBedSleepers':six}
    return report

def pct(n, d):
    return f'{n} ({int(n/d*100+0.5)}%)'

def table(headers, rows):
    return '<div class="data-scroll" tabindex="0" role="region" aria-label="'+escape(headers[0])+'"><table><thead><tr>'+''.join('<th scope="col">'+escape(str(h))+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td>')+escape(str(v))+('</th>' if i==0 else '</td>') for i,v in enumerate(row))+'</tr>' for row in rows)+'</tbody></table></div>'

def guide_paths(lang):
    return ([f'en/tokyo/hotels-for-{n}-guests/index.html' for n in [4,6,8]]+['en/tokyo/apartment-hotels-for-longer-stays/index.html']) if lang=='en' else ([f'ja/tokyo/{n}-guests/index.html' for n in [4,6,8]]+['ja/tokyo/long-stay-apartment-hotels/index.html'])

def url_path(file):
    return '/' + file.removesuffix('index.html') if file.endswith('index.html') else '/' + file

def article(lang, day, stats, template):
    c = COPY[lang]; ja = lang=='ja'
    soup = BeautifulSoup(template, 'html.parser')
    head = copy.deepcopy(soup.head)
    for tag in head.select('title, meta[name="description"], link[rel="canonical"], link[hreflang], meta[property^="og:"], meta[name^="twitter:"], script[type="application/ld+json"]'):
        tag.decompose()
    url = BASE+f'/{lang}/real-beds/'
    extra = f'<title>{escape(c["title"])}</title><meta name="description" content="{escape(c["description"],quote=True)}"><link rel="canonical" href="{url}">'
    extra += ''.join(f'<link rel="alternate" hreflang="{code}" href="{BASE}/{target}/real-beds/">' for code,target in [('en','en'),('ja','ja'),('x-default','en')])
    graph = [{'@type':'Article','headline':c['h1'],'description':c['description'],'inLanguage':lang,'datePublished':day,'dateModified':day,'author':{'@type':'Organization','name':'GROUP STAY JAPAN'},'publisher':{'@type':'Organization','name':'GROUP STAY JAPAN'},'url':url}, {'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'ホーム' if ja else 'Home','item':BASE+'/'},{'@type':'ListItem','position':2,'name':c['h1'],'item':url}]}]
    extra += '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False)+'</script>'
    extra += '<style>.article-body{max-width:960px;padding-top:40px;padding-bottom:48px}.article-body section{margin-bottom:40px}.article-body h2{font-size:clamp(24px,4vw,34px);line-height:1.25}.article-body a{text-decoration:underline;text-underline-offset:3px}.article-result{padding:20px;border-left:5px solid var(--green);background:#e5efdf;font-size:20px;font-weight:700;border-radius:8px}.data-scroll{max-width:100%;overflow-x:auto;margin:20px 0;border:1px solid var(--line);border-radius:12px;background:white}.data-scroll table{border-collapse:collapse;width:100%;min-width:620px}.data-scroll th,.data-scroll td{padding:14px 18px;border-bottom:1px solid var(--line);text-align:left}.data-scroll thead{background:#e5efdf}.data-scroll tbody tr:last-child{font-weight:700}.article-body li{margin:10px 0}.article-links{display:flex;flex-wrap:wrap;gap:12px 24px}.article-breadcrumb{padding:20px 0;overflow-wrap:anywhere}.hero h1{overflow-wrap:anywhere}.hero .lead{margin-bottom:0}@media(max-width:590px){.hero h1{font-size:38px;line-height:1.12}.article-body{padding-top:28px}.article-result{font-size:18px}}</style>'
    head_html = str(head).replace('</head>',extra+'</head>')
    header = copy.deepcopy(soup.header)
    nav = header.select_one('.langs');nav.clear()
    for code,label in [('en','English'),('ja','日本語')]:
        a=soup.new_tag('a',href=BASE+f'/{code}/real-beds/');a.string=label
        if code==lang:a['aria-current']='page'
        nav.append(a)
    footer = str(soup.footer)
    body = f'<nav class="wrap article-breadcrumb" aria-label="{"パンくず" if ja else "Breadcrumb"}"><a href="/">{"ホーム" if ja else "Home"}</a> › <span aria-current="page">{escape(c["h1"])}</span></nav>'
    body += f'<section class="hero"><div class="wrap"><h1>{escape(c["h1"])}</h1><p class="lead">{escape(c["lead"])}</p></div></section><article class="wrap article-body"><p class="article-result">{escape(c["result"])}</p>'
    for i,s in enumerate(c['sections']):
        body+='<section><h2>'+escape(s['heading'])+'</h2>'
        if i==0:
            body+='<ul>'+''.join('<li>'+escape(l)+'</li>' for l in s['lines'][:4])+'</ul><p>'+escape(s['lines'][4])+'</p>'
        elif i==1:
            names=['東京','京都','大阪','北海道','福岡','その他','合計'] if ja else ['Tokyo','Kyoto','Osaka','Hokkaido','Fukuoka','Other areas','All areas']
            nums=list(stats['areas'].values())+[stats['totals']]
            body+=table(['地域','ホテル数','部屋タイプ数','定員いっぱいで全員がベッドで寝られる'] if ja else ['Area','Hotels','Room types','Every guest in a real bed at full capacity'],[[name,a,b,pct(n,b)] for name,(a,b,n) in zip(names,nums)])
        elif i==2:
            names=['2〜3人','4人','5人','6人','7人','8人以上','合計'] if ja else ['2–3 guests','4 guests','5 guests','6 guests','7 guests','8 or more guests','All']
            nums=list(stats['capacityGroups'].values())+[stats['totals'][1:]]
            body+=table(['定員','部屋タイプ数','定員いっぱいで全員がベッドで寝られる'] if ja else ['Room capacity','Room types','Every guest in a real bed at full capacity'],[[name,n,pct(k,n)] for name,(n,k) in zip(names,nums)])
            body+='<p>'+escape(next(l.split('：',1)[1] for l in s['lines'] if l.startswith('表の下：')))+'</p>'
        elif i==3:
            body+='<p>'+escape(s['lines'][0])+'</p>'
            body+=table(['ベッドで寝られない人数','部屋タイプ数'] if ja else ['People without a real bed','Room types'],list(zip(['1人','2人','3人','4人以上'] if ja else ['1','2','3','4 or more'],stats['shortfallPeople1_2_3_4plus'])))
        elif i==4: body+='<p>'+escape(s['lines'][0])+'</p>'
        elif i==5: body+='<ol>'+''.join('<li>'+escape(l)+'</li>' for l in s['lines'])+'</ol>'
        elif i==6:
            labels=['4人','6人','8人','長期滞在'] if ja else ['4 guests','6 guests','8 guests','Longer stays']
            body+='<nav class="article-links">'+''.join(f'<a href="{url_path(p)}">{label}</a>' for p,label in zip(guide_paths(lang),labels))+'</nav>'
        body+='</section>'
    body+='<p>'+escape(c['note'])+'</p></article>'
    return '<!DOCTYPE html>\n<html lang="'+lang+'">'+head_html+'<body>'+str(header)+'<main>'+body+'</main>'+footer+'</body></html>\n'

def insert_after(text, pattern, addition):
    matches=list(re.finditer(pattern,text,re.S))
    require(len(matches)==1, f'Expected one insertion point: {pattern}')
    pos=matches[0].end()
    return text[:pos]+addition+text[pos:]

def build(input_path, day):
    datetime.strptime(day,'%Y-%m-%d')
    home=read(ROOT/'index.html')
    stats=aggregate(input_path,home)  # No HTML writes before all numeric assertions pass.
    changes={}
    template=read(ROOT/'en/tokyo/hotels-for-6-guests/index.html')
    for lang in ['en','ja']:changes[f'{lang}/real-beds/index.html']=article(lang,day,stats,template)
    if 'data-i18n="realBedsArticle"' not in home and 'data-real-beds-article' not in home:
        home=insert_after(home,r'<p\b[^>]*data-i18n="realBedsNote"[^>]*>.*?</p>','<p><a data-i18n="realBedsArticle" data-real-beds-article="" href="/en/real-beds/" style="text-decoration:underline">How we counted, and results by group size →</a></p>')
        # Existing applyLang uses en/ja/zh/ko dictionaries and gsj-language events.
        marker='const pageParams=new URLSearchParams(location.search);'
        translations=['How we counted, and results by group size →','数え方と人数別の結果 →','計算方式與依人數的結果 →','세는 방법과 인원별 결과 →']
        code='/* real-beds-article */'+''.join(f'Object.assign({obj},{{realBedsArticle:{json.dumps(value,ensure_ascii=False)}}});' for obj,value in zip(['ja','zh','ko'],translations[1:]))
        require(home.count(marker)==1,'Home language insertion point missing')
        home=home.replace(marker,code+marker)
        script='<script>/* real-beds-article-link */(()=>{const update=()=>{const a=document.querySelector("[data-real-beds-article]");if(a)a.href=document.querySelector("#lang")?.value==="ja"?"/ja/real-beds/":"/en/real-beds/";};addEventListener("gsj-language",update);update();})();</script>'
        home=home.replace('</body>',script+'</body>')
    changes['index.html']=home
    for lang in ['en','ja']:
        for path in guide_paths(lang):
            text=read(ROOT/path)
            if 'data-real-beds-article' not in text:
                link=f'<p data-real-beds-article=""><a href="/{lang}/real-beds/" style="text-decoration:underline">'+('How we count beds →' if lang=='en' else 'ベッドの数え方 →')+'</a></p>'
                if 'gsj-beds-note' in text:
                    text=insert_after(text,r'<p\b[^>]*class="[^"]*gsj-beds-note[^\"]*"[^>]*>.*?</p>',link)
                else:
                    # Longer-stay hubs have no bed-count note; place next to existing methodology.
                    soup=BeautifulSoup(text,'html.parser')
                    phrase='Kitchen means' if lang=='en' else 'キッチン'
                    candidates=[p for p in soup.find_all('p') if phrase in p.get_text() and ('unverified' in p.get_text() or '未確認' in p.get_text())]
                    require(len(candidates)==1,'Long-stay methodology anchor missing: '+path)
                    anchor=candidates[0].get_text()
                    matching=[m for m in re.finditer(r'<p\b[^>]*>.*?</p>',text,re.S) if BeautifulSoup(m[0],'html.parser').get_text()==anchor]
                    require(len(matching)==1,'Cannot uniquely locate methodology paragraph')
                    pos=matching[0].end();text=text[:pos]+link+text[pos:]
            changes[path]=text
    about=read(ROOT/'_SYSTEM/about.html')
    if 'data-real-beds-article' not in about:
        about=insert_after(about,r'<h1\b[^>]*>.*?</h1>','<p data-real-beds-article=""><a href="/en/real-beds/">Does everyone get a real bed? →</a></p>')
    changes['_SYSTEM/about.html']=about
    xml=read(ROOT/'sitemap-core.xml')
    affected={BASE+url_path(p) for p in ['index.html','_SYSTEM/about.html']+guide_paths('en')+guide_paths('ja')}
    def update(m):
        block=m[0];loc=re.search(r'<loc>(.*?)</loc>',block)[1]
        if loc in affected: return re.sub(r'<lastmod>.*?</lastmod>',f'<lastmod>{day}</lastmod>',block)
        return block
    xml=re.sub(r'<url>.*?</url>',update,xml,flags=re.S)
    for lang in ['en','ja']:
        url=BASE+f'/{lang}/real-beds/'
        if '<loc>'+url+'</loc>' not in xml:xml=xml.replace('</urlset>',f'<url><loc>{url}</loc><lastmod>{day}</lastmod></url></urlset>')
        else:xml=re.sub(r'(<url><loc>'+re.escape(url)+r'</loc><lastmod>).*?(</lastmod>)',lambda m:m[1]+day+m[2],xml)
    ET.fromstring(xml);changes['sitemap-core.xml']=xml
    for file,text in changes.items():
        path=ROOT/file;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(text.encode('utf-8'))
    print(json.dumps(stats,ensure_ascii=False,indent=2))
    print('Written files: '+str(len(changes)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=DEFAULT_INPUT);parser.add_argument('--date',default=datetime.now(timezone(timedelta(hours=9))).date().isoformat())
    args=parser.parse_args();build(args.input,args.date)
