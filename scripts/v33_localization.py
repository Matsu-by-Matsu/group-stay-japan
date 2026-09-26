"""v3.3 presentation-only normalization. Official names and quotations are protected."""
import re,json,unicodedata,statistics,os,subprocess
from functools import lru_cache
from pathlib import Path
from bs4 import BeautifulSoup, Doctype, Comment
AREA={
'Chitose':('Chitose','千歳市'),
'伊勢市':('Ise','伊勢市'),'倉敷市':('Kurashiki','倉敷市'),'函館市':('Hakodate','函館市'),'別府市':('Beppu','別府市'),
'北九州市 / 門司区':('Kitakyushu / Moji','北九州市 / 門司区'),'名古屋市 / 中区':('Nagoya / Naka','名古屋市 / 中区'),
'唐津市':('Karatsu','唐津市'),'宮崎市':('Miyazaki','宮崎市'),'岡山市 / 北区':('Okayama / Kita','岡山市 / 北区'),
'広島市 / 中区':('Hiroshima / Naka','広島市 / 中区'),'広島市 / 南区':('Hiroshima / Minami','広島市 / 南区'),'広島市 / 東区':('Hiroshima / Higashi','広島市 / 東区'),
'札幌市 / 中央区':('Sapporo / Chuo','札幌市 / 中央区'),'熊本市 / 中央区':('Kumamoto / Chuo','熊本市 / 中央区'),
'福岡市 / 中央区':('Fukuoka / Chuo','福岡市 / 中央区'),'福岡市 / 博多区':('Fukuoka / Hakata','福岡市 / 博多区'),
'長崎市':('Nagasaki','長崎市'),'高山市':('Takayama','高山市'),'高松市':('Takamatsu','高松市'),'鹿児島市':('Kagoshima','鹿児島市')}
for city,jcity,wards in [('Tokyo','東京',{'arakawa':'荒川区','chuo':'中央区','minato':'港区','ota':'大田区','shinjuku':'新宿区','sumida':'墨田区','taito':'台東区','toshima':'豊島区'}),('Kyoto','京都市',{'higashiyama':'東山区','minami':'南区','nakagyo':'中京区','shimogyo':'下京区'}),('Osaka','大阪市',{'chuo':'中央区','fukushima':'福島区','higashiyodogawa':'東淀川区','naniwa':'浪速区','nishi':'西区','yodogawa':'淀川区'})]:
 for w,jw in wards.items():AREA[city+' / '+w+'-ku']=(city+' / '+w.title(),jcity+' / '+jw)
def area_label(a,lang='en'):
 if a=='unclassified':return ''
 return AREA[a][1 if lang=='ja' else 0]
BEDS={'semi-double bed':'セミダブルベッド','single loft bed':'シングルロフトベッド','queen bed':'クイーンベッド','double bed':'ダブルベッド','single bed':'シングルベッド','king bed':'キングベッド','daybed':'デイベッド','sofa bed':'ソファベッド','futon':'布団','bunk bed':'二段ベッド','loft bed':'ロフトベッド'}
ALIASES={'クイーン':'queen bed','ダブル':'double bed','セミダブル':'semi-double bed','シングル':'single bed','キング':'king bed','バンクベッド':'bunk bed','二段ベッド':'bunk bed',**{j:e for e,j in BEDS.items()}}
UNKNOWN_BEDS=set();REMOVED={}
def bed_text(raw,lang='en'):
 if not raw:return ''
 s=unicodedata.normalize('NFKC',str(raw));s=s.replace('✕','×');s=re.sub(r'loftbed','loft bed',s,flags=re.I)
 for j,e in sorted(ALIASES.items(),key=lambda x:-len(x[0])):s=s.replace(j,e)
 names='|'.join(re.escape(k) for k in sorted(BEDS,key=len,reverse=True))
 pat=re.compile(r'(?:(\d+)\s*('+names+r')s?\b|('+names+r')s?\s*[x×]\s*(\d+))',re.I)
 def repl(m):
  n=int(m[1] or m[4]);k=(m[2] or m[3]).lower()
  return BEDS[k]+'×'+str(n) if lang=='ja' else f'{n} {k}'+('s' if n!=1 else '')
 s=pat.sub(repl,s)
 if lang=='ja':
  for en,j in sorted(BEDS.items(),key=lambda x:-len(x[0])):s=re.sub(r'\b'+re.escape(en)+r's?\b',j,s,flags=re.I)
 s=re.sub(r'\s*[・、,/]\s*','、' if lang=='ja' else ', ',s)
 s=re.sub(r'(?<=\d)\s+(?=[ァ-ヶ])','、',s) if lang=='ja' else re.sub(r'(?<=beds)\s+(?=\d)|(?<=bed)\s+(?=\d)|(?<=futons)\s+(?=\d)|(?<=futon)\s+(?=\d)',', ',s)
 s=s.strip(' ,、')
 residue=pat.sub('',unicodedata.normalize('NFKC',str(raw)).lower())
 # Audit all unmatched words after converting recognized terms; punctuation/counts are not words.
 audit=s
 for word in list(BEDS)+list(BEDS.values()):audit=re.sub(re.escape(word)+r's?', '',audit,flags=re.I)
 audit=re.sub(r'[\d\s,、・/()（）×x.\-]+','',audit)
 if audit:UNKNOWN_BEDS.add((str(raw),audit))
 return s
REMOVE=['モーダルウィンドウを閉じる']
def clean_quote(s):
 for token in REMOVE:
  if token in s:REMOVED[token]=REMOVED.get(token,0)+s.count(token);s=s.replace(token,'')
 return s

def size_comparison(p,r,brand,area,peers,lang):
 ja=lang=='ja';n=r['capacity'];lines=[]
 if brand:lines.append(f'{p["brand"]}内：{brand[1]}室中{brand[0]}位（1位＝最も広い）' if ja else f'{p["brand"]}: #{brand[0]} of {brand[1]} (#1 = largest)')
 if area:lines.append(f'{area_label(p["areaKey"],lang)}：{area[1]}室中{area[0]}位' if ja else f'{area_label(p["areaKey"],lang)}: #{area[0]} of {area[1]}')
 if peers:
  diff=f'{r["area"]-statistics.mean(peers):+.1f}'.replace('-','−');lines.append(f'{len(peers)}施設の平均との差：{diff} m²' if ja else f'Average across {len(peers)} properties: {diff} m²')
 from html import escape
 return '<div class="size-comparison"><h3>'+ (f'同じ定員（{n}人）の客室との広さの比較' if ja else f'Room size compared with other rooms for {n} guests')+'</h3><ul>'+''.join('<li>'+escape(x)+'</li>' for x in lines)+'</ul></div>'
# English -> Japanese, Traditional Chinese, Korean. Long phrases take priority.
T={}
def add(en,ja,zh,ko):T[en]=(ja,zh,ko)
add('Readiness evidence','判定の根拠','判定依據','판정 근거')
add('Short stay','短期滞在','短期住宿','단기 숙박')
add('Week-ready','5〜9泊向け','適合5至9晚','5~9박 적합')
add('Long-stay ready','10〜19泊向け','適合10至19晚','10~19박 적합')
add('Extended-stay ready','20泊以上向け','適合20晚以上','20박 이상 적합')
add('How stay readiness is checked','連泊適性の判定方法','長住適合度的判定方式','장기 숙박 적합도 판정 방법')
add('published room specifications','公式の客室情報','官方客房資訊','공식 객실 정보')
add('washer','室内洗濯機','室內洗衣機','객실 내 세탁기');add('kitchen','キッチン','廚房','주방');add('cleaning','清掃ルール','清潔規則','청소 규칙');add('extended','20泊以上の規定','20晚以上住宿規定','20박 이상 숙박 규정')
add('Kitchen means the official room description explicitly lists a kitchen. Stove type and burner count are displayed only when confirmed. A missing condition is unverified, not proof of absence. For longer stays, confirm cleaning and linen changes, laundry, kitchen equipment, minimum / maximum nights and the booking conditions. Extended-stay readiness requires an explicit long-stay plan or permission for at least 20 nights.','キッチンは公式の客室説明に明記されている場合に表示します。コンロの種類と口数は確認できた場合のみ表示します。情報がない項目は未確認であり、非対応を意味しません。連泊前に清掃・リネン交換、洗濯設備、キッチン設備、最低・最大泊数、予約条件を確認してください。20泊以上向けの判定には、長期滞在プランまたは20泊以上の滞在可という明記が必要です。','僅在官方客房說明明確列出廚房時標示。爐具種類和爐口數僅在確認後顯示。缺少資訊表示尚未確認，並非不提供。長住前請確認清潔與床單更換、洗衣與廚房設備、最少及最多住宿晚數和預訂條件。20晚以上適合度須有長住方案或明確允許住宿至少20晚的記載。','공식 객실 설명에 주방이 명시된 경우에만 표시합니다. 조리기구 종류와 화구 수는 확인된 경우에만 표시합니다. 정보가 없으면 미확인이며, 미지원이라는 뜻은 아닙니다. 장기 숙박 전 청소와 침구 교체, 세탁·주방 설비, 최소·최대 숙박일 수 및 예약 조건을 확인하세요. 20박 이상 적합 판정에는 장기 숙박 상품 또는 최소 20박 숙박 허용에 관한 명시가 필요합니다.')
add('Cleaning during longer stays — official policies','連泊中の清掃ルール（公式の記載）','長住期間清潔規則（官方記載）','장기 숙박 중 청소 규칙(공식 안내)')
add('Blank cells mean the detail was not confirmed. Conflicting official policies are shown separately.','空欄は詳細未確認です。公式情報に不一致がある場合は両方の記載を表示しています。','空白欄位表示尚未確認。互相矛盾的官方規定會分別列出。','빈칸은 세부 내용 미확인을 뜻합니다. 서로 다른 공식 안내는 각각 표시합니다.')
add('Official information conflict','公式情報の不一致','官方資訊不一致','공식 정보 불일치')
add('Every 7 days after the first service','初回清掃後は7日ごと','首次清潔後每7天一次','첫 청소 이후 7일마다')
add('Every two days; daily towels / vacuuming separately','2日ごと（毎日のタオル交換・掃除機がけは別途記載）','每兩天一次；每日毛巾更換／吸塵另有記載','이틀마다; 매일 수건 교체·진공청소는 별도 안내')
add('Every 3 days','3日ごと','每3天一次','3일마다')
add('Third day (official wording: excluding check-in day)','3日目（公式記載：チェックイン日を除く）','第3天（官方原文：不含入住日）','3일째(공식 안내: 체크인 당일 제외)')
add('Day 4','4日目','第4天','4일째');add('stays of 7+ nights only','7泊以上の滞在のみ','僅限7晚以上住宿','7박 이상 숙박만 해당')
add('Scheduled service: free','定期清掃：無料','定期清潔：免費','정기 청소: 무료');add('Additional service: paid','追加清掃：有料','額外清潔：付費','추가 청소: 유료')
add('Affiliate links: we may receive a commission when you book.','アフィリエイトリンク経由の予約により、当サイトが報酬を受け取る場合があります。','透過聯盟行銷連結預訂時，本站可能獲得佣金。','제휴 링크를 통해 예약하면 사이트가 수수료를 받을 수 있습니다.')
add('Confirm the selected room, dates, guests, room count and final conditions on Trip.com. This page does not display live prices or availability.','選択した客室・日程・人数・部屋数と最終条件はTrip.comで確認してください。このページではリアルタイムの料金・空室状況を表示していません。','請在Trip.com確認所選客房、日期、人數、房間數及最終條件。本頁不顯示即時價格或空房資訊。','선택한 객실·날짜·인원·객실 수와 최종 조건은 Trip.com에서 확인하세요. 이 페이지에는 실시간 요금이나 공실 정보가 표시되지 않습니다.')
for row in [
('First service / eligibility','初回清掃／対象条件','首次清潔／適用條件','첫 청소 / 적용 조건'),('Official statement','公式記載','官方記載','공식 안내'),('Official wording','公式の原文','官方原文','공식 원문'),('Official source','公式出典','官方來源','공식 출처'),('Frequency','頻度','頻率','빈도'),('Free / paid','無料／有料','免費／付費','무료 / 유료'),('Property / room','施設・客室','住宿設施／客房','숙소 / 객실'),('Brand / area','ブランド／エリア','品牌／地區','브랜드 / 지역'),('Sleeping arrangement','ベッド構成','床位配置','침대 구성'),('Area / per guest','面積／1人あたり','面積／每人','면적 / 1인당'),('Bedrooms / baths / toilets','寝室／浴室／トイレ','臥室／浴室／廁所','침실 / 욕실 / 화장실'),('In-room washer / kitchen','室内洗濯機／キッチン','室內洗衣機／廚房','객실 내 세탁기 / 주방'),('Stay readiness','連泊適性','長住適合度','장기 숙박 적합도'),('Capacity','定員','容納人數','정원'),('Source','出典','來源','출처'),('Property','施設','住宿設施','숙소'),('All rooms / 2–4 nights','全客室／2〜4泊','所有客房／2至4晚','전체 객실 / 2~4박'),('Visible room types:','表示中の客室タイプ数：','顯示客房類型數：','표시된 객실 유형 수:'),('5–9 nights','5〜9泊','5至9晚','5~9박'),('10–19 nights','10〜19泊','10至19晚','10~19박'),('10+ nights','10泊以上','10晚以上','10박 이상'),('20+ nights','20泊以上','20晚以上','20박 이상'),('Maximum official room capacity','公式客室の最大定員','官方客房最大容納人數','공식 객실 최대 정원'),('Bed sleepers','ベッド就寝人数','床鋪可睡人數','침대 취침 인원'),('Sofa beds','ソファベッド','沙發床','소파베드'),('Futons','布団','日式床墊','요이불'),('In-room washer','室内洗濯機','室內洗衣機','객실 내 세탁기'),('Kitchen','キッチン','廚房','주방'),('Cleaning policy','清掃ルール','清潔規則','청소 규칙'),('20+ night policy','20泊以上の規定','20晚以上住宿規定','20박 이상 숙박 규정'),('Confirmed','確認済み','已確認','확인됨'),('confirmed','確認済み','已確認','확인됨'),('Not supported','非対応','不提供','미지원'),('not supported','非対応','不提供','미지원'),('Unverified','未確認','尚未確認','미확인'),('unverified','未確認','尚未確認','미확인'),('Yes','あり','有','있음'),('Other stays in','同じエリアの候補：','同地區其他住宿：','같은 지역의 다른 숙소:'),('Stove / IH','コンロ／IH','爐具／電磁爐','가스레인지 / 인덕션'),('Burners','口数','爐口數','화구 수'),('Drying facility','乾燥設備','烘乾設備','건조 설비'),('Microwave','電子レンジ','微波爐','전자레인지'),('Refrigerator','冷蔵庫','冰箱','냉장고'),('Cookware','調理器具','炊具','조리도구'),('Tableware','食器','餐具','식기'),('Room type','客室タイプ','客房類型','객실 유형'),('Check-in','チェックイン','入住日期','체크인'),('Check-out','チェックアウト','退房日期','체크아웃'),('Rooms','部屋数','客房數','객실 수'),('Guests','人数','人數','인원'),('Nights','泊数','晚數','숙박일 수'),('Custom','任意の日数','自訂','직접 설정'),('Check availability on Trip.com','Trip.comで空室を確認','在Trip.com確認空房','Trip.com에서 공실 확인'),('About','このサイトについて','關於本站','사이트 소개'),('Area unverified','面積未確認','面積尚未確認','면적 미확인'),('Sleeping arrangement unverified','ベッド構成未確認','床位配置尚未確認','침대 구성 미확인'),('m² / guest','m²／人','m²／人','m² / 인'),('Feature','項目','項目','항목'),('Apartment hotel','アパートメントホテル','公寓式飯店','아파트먼트 호텔'),('Business hotel','ビジネスホテル','商務飯店','비즈니스호텔'),('Example calculation','計算例','計算範例','계산 예시'),('Apartment hotel, per person','アパートメントホテル・1人あたり','公寓式飯店每人費用','아파트먼트 호텔 1인당 비용'),('Business hotel, per person','ビジネスホテル・1人あたり','商務飯店每人費用','비즈니스호텔 1인당 비용'),('Difference per person','1人あたりの差額','每人差額','1인당 차액'),('Difference for the group','グループ全体の差額','團體總差額','일행 전체 차액'),('This is an example calculation. Actual prices vary by date, season and property.','これは計算例です。実際の料金は日程・季節・施設によって異なります。','此為計算範例。實際價格因日期、季節和住宿設施而異。','계산 예시입니다. 실제 요금은 날짜, 계절, 숙소에 따라 달라집니다.')]:add(*row)

add('bathroom_drying_facility_not_tumble_dryer','浴室乾燥設備（回転式乾燥機ではありません）','浴室乾燥設備（非滾筒烘衣機）','욕실 건조 설비(회전식 건조기 아님)')
add('with Freezer','冷凍庫付き','附冷凍庫','냉동실 포함')
add('microwave','電子レンジ','微波爐','전자레인지')
add('Not a single apartment. Never treat Adults 12 or the combined beds as one room. No combined area calculation.','単独の1室ではありません。大人12人や複数室の寝具合計を1室分として扱わず、合計面積での計算は行いません。','這不是單一客房，不將12名成人或多間客房的床位總數視為一間客房，也不以合計面積計算。','하나의 객실이 아닙니다. 성인 12명이나 여러 객실의 침대 합계를 한 객실로 취급하지 않으며 합산 면적을 계산하지 않습니다.')

@lru_cache(maxsize=30000)
def translate(v,lang):
 if lang=='en':return v
 idx={'ja':0,'zh-Hant':1,'zh-tw':1,'ko':2}[lang]
 if v.strip() in T:return v.replace(v.strip(),T[v.strip()][idx])
 # Dynamic generated summaries, not official text.
 patterns=[(r'Adult capacity excludes a separate official allowance of (\d+) children\. Confirm ages and bed-sharing conditions with the property\.',lambda m:(f'大人定員とは別に、公式記載の子ども{m[1]}人分の枠があります。年齢・添い寝条件は施設に確認してください。',f'成人定員不含官方另列的{m[1]}名兒童名額。請向住宿設施確認年齡及同床條件。',f'성인 정원과 별도로 공식 안내에 어린이 {m[1]}명 허용이 있습니다. 연령과 침대 공유 조건은 숙소에 확인하세요.')[idx]),
 (r'(\d+) adults; children allowance (\d+) separately',lambda m:(f'大人{m[1]}人（別途子ども{m[2]}人枠）',f'{m[1]}名成人；另有{m[2]}名兒童名額',f'성인 {m[1]}명; 어린이 {m[2]}명 별도')[idx]),
 (r'(\d+) (guests|adults)',lambda m:(f'{"大人" if m[2]=="adults" else ""}{m[1]}人',f'{m[1]}名'+('成人' if m[2]=='adults' else '住客'),f'{"성인 " if m[2]=="adults" else ""}{m[1]}명')[idx]),
 (r'(\d+) (bedrooms?|bathrooms?|toilets?)',lambda m: (f'{ {"bedroom":"寝室","bathroom":"浴室","toilet":"トイレ"}[m[2].rstrip("s")]}{m[1]}室',f'{m[1]}間'+{'bedroom':'臥室','bathroom':'浴室','toilet':'廁所'}[m[2].rstrip('s')],f'{ {"bedroom":"침실","bathroom":"욕실","toilet":"화장실"}[m[2].rstrip("s")]} {m[1]}개')[idx])]
 for pattern,fn in patterns:v=re.sub(pattern,fn,v)
 keys=sorted(T,key=len,reverse=True)
 # One substitution pass avoids translating words introduced by another translation.
 pat=re.compile('|'.join(re.escape(k) for k in keys))
 return pat.sub(lambda m:T[m[0]][idx],v)

def localize(markup,lang,protected_names=()):
 soup=BeautifulSoup(markup,'html.parser');names=set(protected_names)
 for node in list(soup.find_all(string=True)):
  if isinstance(node,(Doctype,Comment)):continue
  if any(p.name in ['script','style'] or p.has_attr('data-official-name') or p.has_attr('data-official-quote') for p in node.parents):continue
  if str(node).strip() in names:continue
  node.replace_with(translate(str(node),lang))
 return str(soup)

def load_approved_f(root,example):
 draft=(root/'review/F-TRANSLATION-DRAFTS.md').read_text(encoding='utf8')
 en=BeautifulSoup(example('hub'),'html.parser');english_rows=[[c.get_text() for c in tr.find_all(['th','td'])] for tr in en.select('table')[0].select('tr')]
 chunks=re.split(r'^## (?:日本語|繁體中文|한국어)\s*$',draft,flags=re.M)[1:]
 for idx,chunk in enumerate(chunks):
  blocks=re.split(r'^### .*$',chunk,flags=re.M)[1:]
  hub=blocks[2].strip();paras=hub.split('\n\n');addval=lambda en,txt:T.setdefault(en,['','',''])
  head=paras[0];key='Apartment hotel vs. business hotel for groups';T.setdefault(key,['','','']);T[key]=list(T[key]);T[key][idx]=head
  rows=[line.strip('|').split('|') for line in hub.splitlines() if line.startswith('|') and not line.startswith('|---')]
  for ens,trs in zip(english_rows,rows):
   for a,b in zip(ens,trs):
    b=b.replace('通常毎日','毎日の場合が多い').replace('通常每天提供','多為每天提供').replace('보통 매일 제공','매일 제공되는 경우가 많음')
    T.setdefault(a,['','','']);T[a]=list(T[a]);T[a][idx]=b
  ep=en.find('p').get_text();text=next(p for p in paras if p.startswith(('フロント','如果','직원이')));T.setdefault(ep,['','','']);T[ep]=list(T[ep]);T[ep][idx]=text
  premise=next(p for p in paras if p.startswith(('計算例：','計算範例：','계산 예시:'))).split('\n')[0].split('：',1)[-1] if idx<2 else next(p for p in paras if p.startswith('계산 예시:')).split('\n')[0].removeprefix('계산 예시: ')
  key='One unit for 6 guests at ¥60,000 per night, compared with one business hotel single room per guest at ¥12,000–14,000 per night.';T.setdefault(key,['','','']);T[key]=list(T[key]);T[key][idx]=premise
 return chunks

def finalize(root,P,urls,example,comparison,criteria,cleaning,tokyo,enhance):
 chunks=load_approved_f(root,example)
 # Existing non-English size lists: add approved F copy, no new URL or title/H1 changes.
 for lang,folder,idx in [('ja','ja',0),('zh-Hant','zh-tw',1),('ko','ko',2)]:
  block=re.split(r'^### .*$',chunks[idx],flags=re.M)[2].strip().split('\n\n');heading,copy=block[0],block[1]
  for n in [4,6,8]:
   path=f'{folder}/tokyo/hotels-for-{n}-guests/index.html'
   if not (root/path).exists():continue
   fs=BeautifulSoup(example(),'html.parser');fs.h2.decompose();fs.find('p').decompose()
   content='<h2>'+heading.replace('{N}',str(n)).replace('{R}',str(n//2))+'</h2><p>'+copy.replace('{N}',str(n)).replace('{R}',str(n//2))+'</p>'+str(fs)
   enhance(path,content)
  for u in urls:
   if '/'+folder+'/' not in u or 'long' not in u:continue
   f=root/(u.split('synthx.jp/')[1].strip('/')+'/index.html');s=BeautifulSoup(f.read_text(encoding='utf8'),'html.parser');part=s.select_one('.gsj-v31');part.insert(0,BeautifulSoup(example('hub'),'html.parser'));f.write_text(str(s),encoding='utf8')
 protected=[p['name'] for p in P]+[r['name'] for p in P for r in p['rooms']]
 for p in P:
  for lang in ['en','ja']:
   f=root/((('ja/' if lang=='ja' else '')+'stays/'+p['id']+'/index.html'));s=BeautifulSoup(f.read_text(encoding='utf8'),'html.parser')
   # Excluded notice language, official names and quotations remain untouched.
   if p['excluded']:
    w=s.select_one('.warning');w.clear();w.append('公式サイトで掲載を確認できません（2026年9月25日時点）。比較表・集計・候補から除外しています。' if lang=='ja' else 'This property could not be confirmed on the official website as of September 25, 2026. It is excluded from comparisons and recommendations.')
   f.write_text(localize(str(s),lang,protected),encoding='utf8')
 for u in urls:
  if '/stays/' in u:continue
  lang='ja' if '/ja/' in u else 'zh-Hant' if '/zh-tw/' in u else 'ko' if '/ko/' in u else 'en'
  if lang=='en':continue
  f=root/(u.split('synthx.jp/')[1].strip('/')+'/index.html')
  if not f.exists():continue
  s=BeautifulSoup(f.read_text(encoding='utf8'),'html.parser')
  for part in s.select('.gsj-v31'):part.replace_with(BeautifulSoup(localize(str(part),lang,protected),'html.parser'))
  f.write_text(str(s),encoding='utf8')
 # lastmod only for HTML changed versus original production HEAD; no speculative publication date.
 changed=[]
 for u in urls:
  path=u.split('synthx.jp/')[1];path=(path+'index.html') if not path or path.endswith('/') else path
  f=root/path
  old=subprocess.run(['git','show','HEAD:'+path],cwd=root,capture_output=True).stdout
  if f.exists() and old.replace(b'\r\n',b'\n')!=f.read_bytes().replace(b'\r\n',b'\n'):changed.append(u)
 date=os.environ.get('GSJ_PUBLISH_DATE')
 if date:write_lastmod(root,changed,date)
 (root/'review/lastmod-pending-urls.json').write_text(json.dumps(changed,indent=2),encoding='utf8')
 (root/'review/v33-mappings.json').write_text(json.dumps({'areas':AREA,'translations':T,'beds':BEDS,'unknownBedTerms':sorted(UNKNOWN_BEDS),'removedQuoteText':REMOVED,'lastmodDate':date},ensure_ascii=False,indent=2),encoding='utf8')


def write_lastmod(root,changed,date):
 import datetime
 datetime.date.fromisoformat(date)
 for name in ['sitemap-core.xml','sitemap-stays-en.xml','sitemap-stays-ja.xml']:
  f=root/name;s=BeautifulSoup(f.read_text(encoding='utf8'),'xml')
  for item in s.find_all('url'):
   for old in item.find_all('lastmod'):old.decompose()
   if item.loc.text in changed:
    t=s.new_tag('lastmod');t.string=date;item.append(t)
  f.write_text(str(s),encoding='utf8')
