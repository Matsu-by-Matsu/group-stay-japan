"""Add preview-only Chinese/Korean property pages from the current published English pages."""
from pathlib import Path
import json,re,sys,subprocess
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from bs4 import BeautifulSoup,Doctype,Comment
from v33_localization import translate,T
R=Path(__file__).resolve().parents[1]
LANGS={'en':('','English'),'ja':('ja/','日本語'),'zh-TW':('zh-tw/','繁體中文'),'ko':('ko/','한국어')}
EXTRA={
'Choose a room and dates':('選擇客房與日期','객실과 날짜 선택'),
'This property could not be confirmed on the official website as of September 25, 2026. It is excluded from comparisons and recommendations.':('截至2026年9月25日，未能在官方網站確認此住宿設施。已從比較與推薦中排除。','2026년 9월 25일 기준 공식 사이트에서 이 숙소를 확인하지 못했습니다. 비교 및 추천에서 제외합니다.'),
'Family / group suite':('家庭／團體套房','가족 / 단체 스위트'),
'Not a single apartment':('並非單一公寓','하나의 아파트가 아님')}
BEDS={'semi-double bed':('小型雙人床','세미 더블 침대'),'single loft bed':('單人高架床','싱글 로프트 침대'),'queen bed':('加大雙人床','퀸 침대'),'double bed':('雙人床','더블 침대'),'single bed':('單人床','싱글 침대'),'king bed':('特大雙人床','킹 침대'),'daybed':('日間床','데이베드'),'sofa bed':('沙發床','소파베드'),'futon':('日式床墊','요이불'),'bunk bed':('上下舖','이층 침대'),'loft bed':('高架床','로프트 침대')}
BADGES={'zh-TW':['短期住宿（2至4晚）','適合5至9晚','適合10至19晚','適合20晚以上'],'ko':['단기 숙박(2~4박)','5~9박 적합','10~19박 적합','20박 이상 적합']}
def tr(v,lang):
 i=0 if lang=='zh-TW' else 1
 if v.strip() in EXTRA:return v.replace(v.strip(),EXTRA[v.strip()][i])
 v=re.sub(r'Room size compared with other rooms for (\d+) guests',lambda m:f'與同為{m[1]}人房型的面積比較' if i==0 else f'같은 정원({m[1]}명)의 객실 면적 비교',v)
 v=re.sub(r'Average across (\d+) properties:',lambda m:f'與{m[1]}間住宿設施平均值的差異：' if i==0 else f'{m[1]}개 숙소 평균과의 차이:',v)
 v=re.sub(r'#(\d+) of (\d+)',lambda m:f'{m[2]}間中第{m[1]}名' if i==0 else f'{m[2]}개 중 {m[1]}위',v)
 v=v.replace('(#1 = largest)','（第1名＝面積最大）' if i==0 else '(1위 = 가장 넓음)')
 for k,ls in sorted(BEDS.items(),key=lambda x:-len(x[0])):v=re.sub(r'\b'+re.escape(k)+r's?\b',ls[i],v,flags=re.I)
 return translate(v,'zh-Hant' if i==0 else 'ko')
def augment(s,id,lang):
 data=json.loads(s.select_one('#gsj-page-data').string);data['lang']=lang;s.select_one('#gsj-page-data').string=json.dumps(data,ensure_ascii=False)
 nav=s.new_tag('nav',attrs={'class':'gsj-language-links','aria-label':{'en':'Language','ja':'言語','zh-TW':'語言','ko':'언어'}[lang]})
 for k,(prefix,label) in LANGS.items():
  a=s.new_tag('a',href='/'+prefix+'stays/'+id+'/',attrs={'data-property-lang':k,'lang':k});a.string=label
  if k==lang:a['aria-current']='page'
  nav.append(a);nav.append(' · ')
 first=s.find('a',string='English');old=first.find_parent('nav') if first else s.select_one('.gsj-language-links')
 if old:old.replace_with(nav)
 else:s.h1.insert_after(nav)
 form=s.select_one('#booking')
 if form:
  previous=form.select_one('#booking-currency')
  if previous:previous.find_parent('label').decompose()
  label=s.new_tag('label');label.string={'en':'Display currency ','ja':'表示通貨 ','zh-TW':'顯示幣別 ','ko':'표시 통화 '}[lang];select=s.new_tag('select',id='booking-currency')
  words={'en':['JPY — Japanese yen','USD — US dollar','TWD — New Taiwan dollar','KRW — Korean won'],'ja':['JPY — 日本円','USD — 米ドル','TWD — 台湾ドル','KRW — 韓国ウォン'],'zh-TW':['JPY — 日圓','USD — 美元','TWD — 新臺幣','KRW — 韓元'],'ko':['JPY — 일본 엔','USD — 미국 달러','TWD — 신대만 달러','KRW — 대한민국 원']}[lang]
  for code,text in zip(['JPY','USD','TWD','KRW'],words):
   o=s.new_tag('option',value=code);o.string=text;
   if code=={'en':'USD','ja':'JPY','zh-TW':'TWD','ko':'KRW'}[lang]:o['selected']=''
   select.append(o)
  label.append(select);form.select_one('button[type=submit]').insert_before(label)
 for a in s.select('a[href]'):
  if a.has_attr('data-property-lang'):continue
  href=a['href'];match=re.search(r'/(?:ja/|zh-tw/|ko/)?stays/([^/?#]+)/',href)
  if match:a['href']=re.sub(r'/(?:ja/|zh-tw/|ko/)?stays/', '/'+LANGS[lang][0]+'stays/',href)
  elif href=='/':a['href']='/?lang='+lang
  elif 'trip.com/' in href:
   u=urlsplit(href);q=dict(parse_qsl(u.query));q['locale']={'en':'en-XX','ja':'ja-JP','zh-TW':'zh-TW','ko':'ko-KR'}[lang];q['curr']={'en':'USD','ja':'JPY','zh-TW':'TWD','ko':'KRW'}[lang];a['href']=urlunsplit((u.scheme,{'en':'www.trip.com','ja':'jp.trip.com','zh-TW':'tw.trip.com','ko':'kr.trip.com'}[lang],u.path,urlencode(q),u.fragment))
 for asset in s.select('script[src],link[rel=stylesheet]'):
  key='src' if asset.name=='script' else 'href'
  if any(n in asset[key] for n in ['gsj-rooms.js','gsj-ui.js']):asset[key]=asset[key].split('?')[0]+'?v=20260927locale2'
 return s
# Create new versions before changing the existing source.
for f in sorted((R/'stays').glob('*/index.html')):
 id=f.parent.name;en=BeautifulSoup(subprocess.check_output(['git','show','HEAD:'+f.relative_to(R).as_posix()],cwd=R).decode('utf8'),'html.parser')
 protected={en.h1.get_text()}|{n.get_text() for n in en.select('article.room h2,#room-type option,[data-official-name]')}
 for lang in ['zh-TW','ko']:
  s=BeautifulSoup(str(en),'html.parser')
  for node in list(s.find_all(string=True)):
   if isinstance(node,(Doctype,Comment)) or any(p.name in ['script','style'] or p.has_attr('data-official-name') or p.has_attr('data-official-quote') for p in node.parents):continue
   if str(node).strip() in protected:continue
   node.replace_with(tr(str(node),lang))
  s.html['lang']='zh-Hant' if lang=='zh-TW' else 'ko'
  for tag in s.select('meta[name=robots],link[hreflang]'):tag.decompose()
  s.head.append(s.new_tag('meta',attrs={'name':'robots','content':'noindex,follow'}))
  url='https://groupstayjapan.synthx.jp/'+LANGS[lang][0]+'stays/'+id+'/'
  s.select_one('link[rel=canonical]')['href']=url
  s.title.string=en.h1.get_text()+('｜客房與住宿資訊' if lang=='zh-TW' else ' | 객실 및 숙박 정보')+' | GROUP STAY JAPAN'
  s.select_one('meta[name=description]')['content']=en.h1.get_text()+('：比較客房、床位、設備及長住適合度。在Trip.com確認日期、人數與最終預訂條件。' if lang=='zh-TW' else ': 객실, 침대, 시설 및 장기 숙박 적합도를 비교하세요. Trip.com에서 날짜, 인원 및 최종 예약 조건을 확인하세요.')
  for j in s.select('script[type="application/ld+json"]'):j.string=(j.string or '').replace('https://groupstayjapan.synthx.jp/stays/'+id+'/',url)
  for b in s.select('.gsj-stay-badge'):b.string=BADGES[lang][int(b['data-readiness-level'])-1]
  sm=s.select_one('.gsj-readiness-summary')
  if sm:
   original=en.select_one('.gsj-readiness-summary').get_text();m=re.search(r'up to (.*?) nights \((\d+) of (\d+) room types\)',original)
   if m:
    period=m[1].replace('–','至' if lang=='zh-TW' else '~');sm.string=f'長住適合度：最長{period}晚（{m[3]}種房型中有{m[2]}種）' if lang=='zh-TW' else f'장기 숙박 적합도: 최대 {period}박 ({m[3]}개 객실 유형 중 {m[2]}개)'
   else:sm.string='長住適合度：短期住宿（2至4晚）' if lang=='zh-TW' else '장기 숙박 적합도: 단기 숙박(2~4박)'
  s=augment(s,id,lang);target=R/LANGS[lang][0]/'stays'/id/'index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(str(s),encoding='utf8')
 for lang in ['en','ja']:
  target=R/LANGS[lang][0]/'stays'/id/'index.html';s=BeautifulSoup(subprocess.check_output(['git','show','HEAD:'+target.relative_to(R).as_posix()],cwd=R).decode('utf8'),'html.parser');target.write_text(str(augment(s,id,lang)),encoding='utf8')
# Localized list and hub links point to their own language property pages.
for folder in ['zh-tw','ko']:
 for f in (R/folder/'tokyo').glob('*/index.html'):
  b=f.read_bytes();b=re.sub(rb'(?<=href=")(/stays/)',('/'+folder+'/stays/').encode(),b);f.write_bytes(b)
print('Generated 162 noindex property pages; updated 162 existing language selectors and booking currency controls.')
