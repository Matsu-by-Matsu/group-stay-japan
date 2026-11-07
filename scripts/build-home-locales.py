#!/usr/bin/env python3
"""Build static Korean/Traditional Chinese home pages and their home links."""
import argparse, json, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from html import escape
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://groupstayjapan.synthx.jp"
TEXT = {
  "ko": {
    "title": "일본 가족·단체 여행 숙소 비교 | 4인·6인·8인 아파트먼트 호텔 | GROUP STAY JAPAN",
    "description": "일본 아파트먼트 호텔 78곳, 객실 유형 446개를 공식 정보로 비교합니다. 정원과 침대 구성, 주방, 세탁기를 객실별로 확인할 수 있습니다.",
    "h1": "일본 가족·단체 여행을 위한 아파트먼트 호텔",
    "lead": "3명 이상의 가족과 친구가 한 객실에 함께 묵을 수 있는 일본의 아파트먼트 호텔을 모았습니다. 정원, 침대 구성, 주방과 세탁기는 각 호텔의 공식 정보로 객실마다 확인했습니다.",
    "h2": [
      "모두 침대에서 잘 수 있을까?",
      "도쿄 인원별 숙소",
      "지역별 숙소",
      "날짜와 인원으로 찾기"
    ],
    "p": [
      "6명이 묵을 수 있는 객실이라고 해서 침대가 6명분 있는 것은 아닙니다. 객실 유형 446개 중 정원이 다 차도 모두 침대에서 잘 수 있는 객실은 259개(58%)입니다.",
      "숙소 이름을 누르면 객실별 정원, 침대 구성, 주방과 세탁기를 볼 수 있습니다.",
      "날짜와 인원을 넣어 검색하려면 검색 화면을 이용하세요. 최종 요금과 예약은 Trip.com에서 확인합니다."
    ],
    "tableHeads": [
      "지역",
      "호텔 수",
      "객실 유형 수",
      "정원이 다 차도 모두 침대에서 잘 수 있는 객실"
    ],
    "rows": [
      [
        "도쿄",
        "26",
        "146",
        "86 (59%)"
      ],
      [
        "교토",
        "14",
        "103",
        "35 (34%)"
      ],
      [
        "오사카",
        "9",
        "53",
        "27 (51%)"
      ],
      [
        "홋카이도",
        "3",
        "21",
        "15 (71%)"
      ],
      [
        "후쿠오카",
        "5",
        "19",
        "16 (84%)"
      ],
      [
        "그 외 지역",
        "21",
        "104",
        "80 (77%)"
      ],
      [
        "합계",
        "78",
        "446",
        "259 (58%)"
      ]
    ],
    "note": "계산 방법: 싱글·세미더블·로프트 침대는 1명, 더블·퀸·킹 침대는 2명, 2층 침대는 1대에 2명. 소파베드·데이베드·요이불은 따로 셉니다. 침대 구성은 공식 사이트 기준(2026/9/25 확인).",
    "links": [
      [
        "자세한 결과(영어) →",
        "/en/real-beds/"
      ],
      [
        "검색 화면으로 →",
        "/?lang=ko"
      ]
    ],
    "guides": [
      [
        "도쿄 4인 가족과 그룹을 위한 호텔",
        "/ko/tokyo/4-guests/"
      ],
      [
        "도쿄에서 6명이 함께 머물 수 있는 호텔",
        "/ko/tokyo/6-guests/"
      ],
      [
        "도쿄 8인과 두 가족을 위한 호텔",
        "/ko/tokyo/8-guests/"
      ],
      [
        "도쿄 주방·세탁 시설 아파트먼트 호텔",
        "/ko/tokyo/long-stay-apartment-hotels/"
      ]
    ],
    "footer": "제휴 안내: 조건에 맞는 예약이 완료되면 여행자의 추가 비용 없이 GROUP STAY JAPAN이 수수료를 받을 수 있습니다.",
    "about": "사이트 소개"
  },
  "zh-tw": {
    "title": "日本家庭與團體旅行住宿比較｜可住4人、6人、8人的公寓式飯店 | GROUP STAY JAPAN",
    "description": "依官方資訊比較日本78間公寓式飯店、446種房型。可依房型確認入住人數、床型、廚房與洗衣機。",
    "h1": "適合日本家庭與團體旅行的公寓式飯店",
    "lead": "整理日本可讓3人以上的家人與朋友同住一間客房的公寓式飯店。入住人數、床型、廚房與洗衣機，皆依各飯店的官方資訊逐一確認。",
    "h2": [
      "每個人都有床可睡嗎？",
      "東京依人數找住宿",
      "依地區找住宿",
      "依日期與人數搜尋"
    ],
    "p": [
      "可住6人的房型，不一定有6人份的床。446種房型中，滿房時全員都有床可睡的有259種（58%）。",
      "點選住宿名稱，即可查看各房型的入住人數、床型、廚房與洗衣機。",
      "若要輸入日期與人數搜尋，請使用搜尋頁面。最終價格與預訂請在Trip.com確認。"
    ],
    "tableHeads": [
      "地區",
      "飯店數",
      "房型數",
      "滿房時全員都有床可睡"
    ],
    "rows": [
      [
        "東京",
        "26",
        "146",
        "86 (59%)"
      ],
      [
        "京都",
        "14",
        "103",
        "35 (34%)"
      ],
      [
        "大阪",
        "9",
        "53",
        "27 (51%)"
      ],
      [
        "北海道",
        "3",
        "21",
        "15 (71%)"
      ],
      [
        "福岡",
        "5",
        "19",
        "16 (84%)"
      ],
      [
        "其他地區",
        "21",
        "104",
        "80 (77%)"
      ],
      [
        "合計",
        "78",
        "446",
        "259 (58%)"
      ]
    ],
    "note": "計算方式：單人床、小雙人床、閣樓床各算1人；雙人床、加大雙人床、特大雙人床各算2人；上下舖每組算2人。沙發床、坐臥兩用床、日式床墊另計。床型依官方網站（2026/9/25確認）。",
    "links": [
      [
        "詳細結果（英文）→",
        "/en/real-beds/"
      ],
      [
        "前往搜尋頁面 →",
        "/?lang=zh-TW"
      ]
    ],
    "guides": [
      [
        "東京適合4人家庭與4人團體的飯店",
        "/zh-tw/tokyo/4-guests/"
      ],
      [
        "東京可供6人一起入住的飯店",
        "/zh-tw/tokyo/6-guests/"
      ],
      [
        "東京適合8人與兩個家庭的飯店",
        "/zh-tw/tokyo/8-guests/"
      ],
      [
        "東京有廚房與洗衣設備的公寓式飯店",
        "/zh-tw/tokyo/long-stay-apartment-hotels/"
      ]
    ],
    "footer": "聯盟行銷說明：符合條件的預訂成立時，GROUP STAY JAPAN可能獲得佣金，旅客不需支付額外費用。",
    "about": "關於本站"
  }
}

ALTERNATES = {'en': '/', 'ko': '/ko/', 'zh-Hant': '/zh-tw/', 'x-default': '/'}

def read(path):
    return path.read_bytes().decode('utf-8')

def save(path, text):
    old = read(path) if path.exists() else None
    if old == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode('utf-8'))
    return True

def anchor(url, text):
    return f'<a href="{escape(url, quote=True)}">{escape(text)}</a>'

def home(lang, data):
    t = TEXT[lang]
    code = 'ko' if lang == 'ko' else 'zh-Hant'
    short = 'ko' if lang == 'ko' else 'zh'
    url = ORIGIN + '/' + lang + '/'
    template = BeautifulSoup(read(ROOT / lang / 'tokyo/4-guests/index.html'), 'lxml')
    head = '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    head += ''.join(str(x) for x in template.head.select('script:not([type]), style, link[rel="stylesheet"]'))
    head += f'<title>{escape(t["title"])}</title><meta name="description" content="{escape(t["description"], quote=True)}"><link rel="canonical" href="{url}">'
    head += ''.join(f'<link rel="alternate" hreflang="{k}" href="{ORIGIN}{v}">' for k,v in ALTERNATES.items())
    for key,value in {'title':t['title'],'description':t['description'],'url':url,'image':ORIGIN+'/assets/hero.jpg','type':'website'}.items():
        head += f'<meta property="og:{key}" content="{escape(value, quote=True)}">'
    head += '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'WebSite','name':'GROUP STAY JAPAN','url':url,'inLanguage':code},ensure_ascii=False)+'</script>'
    header = template.header
    header.select_one('.brand')['href'] = '/'+lang+'/'
    nav = header.select_one('.langs');nav.clear()
    for target,label in [('/','English'),('/zh-tw/','繁體中文'),('/ko/','한국어')]:
        a = template.new_tag('a',href=target);a.string=label
        if target == '/'+lang+'/': a['aria-current']='page'
        nav.append(a)
    body = str(header)+f'<main><section class="hero"><div class="wrap"><h1>{escape(t["h1"])}</h1><p class="lead">{escape(t["lead"])}</p></div></section>'
    body += f'<section class="guide"><div class="wrap"><h2>{t["h2"][0]}</h2><p>{t["p"][0]}</p>'
    body += '<div style="max-width:100%;overflow-x:auto" tabindex="0"><table style="min-width:600px;width:100%;border-collapse:collapse"><thead><tr>'
    body += ''.join(f'<th scope="col" style="text-align:left;padding:12px;border-bottom:1px solid var(--line)">{h}</th>' for h in t['tableHeads'])+'</tr></thead><tbody>'
    for row in t['rows']:
        body += '<tr>'+f'<th scope="row" style="text-align:left;padding:12px;border-bottom:1px solid var(--line)">{row[0]}</th>'+''.join(f'<td style="padding:12px;border-bottom:1px solid var(--line)">{x}</td>' for x in row[1:])+'</tr>'
    body += '</tbody></table></div><p class="small">'+t['note']+'</p><p>'+anchor(t['links'][0][1],t['links'][0][0])+'</p></div></section>'
    body += '<section class="content"><div class="wrap head"><h2>'+t['h2'][1]+'</h2><ul>'+''.join('<li>'+anchor(url,label)+'</li>' for label,url in t['guides'])+'</ul></div></section>'
    body += '<section class="guide" id="regional-stays"><div class="wrap"><h2>'+t['h2'][2]+'</h2><p>'+t['p'][1]+'</p>'
    for group in data['order']:
        stays=[x for x in data['stays'] if x['group']==group]
        title=data['groups'][group][short]+(f' ({len(stays)}곳)' if lang=='ko' else f'（{len(stays)}間）')
        body += '<section><h3>'+title+'</h3><ul style="padding-left:20px;overflow-wrap:anywhere">'
        for x in stays:
            assert (ROOT/lang/'stays'/x['slug']/'index.html').exists(), x['slug']
            capacity=f'최대 {x["max"]}인' if lang=='ko' else f'最多可住{x["max"]}人'
            body+='<li style="margin:10px 0">'+anchor('/'+lang+'/stays/'+x['slug']+'/',x['name'])+' · '+escape(x['area_'+short])+' · '+capacity+'</li>'
        body+='</ul></section>'
    body+='</div></section><section class="content"><div class="wrap head"><h2>'+t['h2'][3]+'</h2><p>'+t['p'][2]+'</p><p>'+anchor(t['links'][1][1],t['links'][1][0])+'</p></div></section></main>'
    footer=template.footer
    footer.select_one('a')['href']='/'+lang+'/'
    footer.select_one('p').string=t['footer']
    other=footer.select('a')[-1];other['href']='/_SYSTEM/about.html';other.string=t['about']
    return '<!DOCTYPE html>\n<html lang="'+code+'"><head>'+head+'</head><body>'+body+str(footer)+'</body></html>\n'

def update_home_links(raw, lang):
    home_path='/'+lang+'/'
    names={'GROUP STAY JAPAN','← GROUP STAY JAPAN','홈' if lang=='ko' else '首頁'}
    def link(m):
        a=BeautifulSoup(m[0],'lxml').a
        if a.get_text(strip=True) in names and a.get('href') in ['/', '/?lang=ko', '/?lang=zh-TW']:
            return re.sub(r'href=("|\').*?\1', 'href="'+home_path+'"',m[0],count=1)
        return m[0]
    raw=re.sub(r'<a\b[^>]*>.*?</a>',link,raw,flags=re.S)
    def ld(m):
        value=json.loads(m[2]);changed=False
        def walk(obj):
            nonlocal changed
            if isinstance(obj,dict):
                if obj.get('@type')=='BreadcrumbList':
                    for item in obj.get('itemListElement',[]):
                        if item.get('position')==1 and item.get('item')==ORIGIN+'/':item['item']=ORIGIN+home_path;changed=True
                for v in obj.values():walk(v)
            elif isinstance(obj,list):
                for v in obj:walk(v)
        walk(value)
        return m[1]+json.dumps(value,ensure_ascii=False)+m[3] if changed else m[0]
    return re.sub(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)',ld,raw,flags=re.S)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--date',default=datetime.now(timezone(timedelta(hours=9))).date().isoformat());args=parser.parse_args()
    datetime.strptime(args.date,'%Y-%m-%d')
    data=json.loads(read(ROOT/'config/home-stays.json'));assert len(data['stays'])==78
    changed=[]
    for lang in ['ko','zh-tw']:
        for path in sorted((ROOT/lang/'stays').glob('*/index.html'))+sorted((ROOT/lang/'tokyo').glob('*/index.html')):
            if save(path,update_home_links(read(path),lang)):changed.append(path.relative_to(ROOT).as_posix())
        path=ROOT/lang/'index.html'
        if save(path,home(lang,data)):changed.append(path.relative_to(ROOT).as_posix())
    path=ROOT/'index.html';raw=read(path)
    for lang,route in [('ko','/ko/'),('zh-Hant','/zh-tw/')]:
        if not re.search('hreflang="'+lang+'"',raw):raw=raw.replace('</head>',f'<link rel="alternate" hreflang="{lang}" href="{ORIGIN}{route}"/></head>',1)
    if 'data-home-locales' not in raw:
        raw=raw.replace('</footer>','<p data-home-locales="" style="text-align:center"><a href="/ko/" lang="ko">한국어</a> · <a href="/zh-tw/" lang="zh-Hant">繁體中文</a></p></footer>',1)
    if save(path,raw):changed.append('index.html')
    changed_urls={ORIGIN+'/'+x.removesuffix('index.html') for x in changed}
    dates=[]
    for path in sorted(ROOT.glob('sitemap*.xml')):
        raw=read(path)
        if path.name=='sitemap-core.xml':
            for lang in ['ko','zh-tw']:
                url=ORIGIN+'/'+lang+'/'
                if '<loc>'+url+'</loc>' not in raw:
                    raw=raw.replace('</urlset>',f'<url><loc>{url}</loc><lastmod>{args.date}</lastmod></url></urlset>');dates.append(url)
        def date(m):
            url=re.search(r'<loc>(.*?)</loc>',m[0])[1]
            if url not in changed_urls:return m[0]
            updated=re.sub(r'<lastmod>.*?</lastmod>',f'<lastmod>{args.date}</lastmod>',m[0])
            if updated!=m[0]:dates.append(url)
            return updated
        raw=re.sub(r'<url>.*?</url>',date,raw,flags=re.S);save(path,raw)
    path=ROOT/'README.md';raw=read(path)
    if 'scripts/build-home-locales.py' not in raw:
        newline='\r\n' if '\r\n' in raw else '\n'
        save(path,raw+newline+'生成のあとに `python scripts/build-home-locales.py --date YYYY-MM-DD` を実行する。'+newline)
    print(json.dumps({'changedPages':len(changed),'lastmodUpdatedOrAdded':len(dates),'date':args.date},ensure_ascii=False))

if __name__=='__main__':
    main()
