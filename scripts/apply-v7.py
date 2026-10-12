"""v7 incremental generator: apply to current production HTML, never rebuild old v3.
Run after other page generators. Keeps a private byte baseline for review.
"""
import argparse, json, re, subprocess, zipfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
from bs4 import BeautifulSoup, Comment, Doctype
R=Path(__file__).resolve().parents[1]
BASE='https://groupstayjapan.synthx.jp'
LANGS=['en','ja','zh-tw','ko']; HOME=['Home','トップ','首頁','홈']
AREA={}
for en,zh,ko in [('Tokyo','東京','도쿄'),('Kyoto','京都','교토'),('Osaka','大阪','오사카'),('Hokkaido','北海道','홋카이도'),('Fukuoka','福岡','후쿠오카'),('Hiroshima','廣島','히로시마'),('Kagoshima','鹿兒島','가고시마'),('Kumamoto','熊本','구마모토'),('Miyazaki','宮崎','미야자키'),('Nagasaki','長崎','나가사키'),('Gifu','岐阜','기후'),('Kagawa','香川','가가와'),('Mie','三重','미에'),('Oita','大分','오이타'),('Saga','佐賀','사가'),('Okayama','岡山','오카야마'),('Aichi','愛知','아이치'),('Japan','日本','일본'),('Hakodate','函館','하코다테'),('Ise','伊勢','이세'),('Takayama','高山','다카야마'),('Takamatsu','高松','다카마쓰'),('Beppu','別府','벳푸'),('Chitose','千歲','치토세'),('Kurashiki','倉敷','구라시키'),('Kitakyushu','北九州','기타큐슈'),('Karatsu','唐津','가라쓰'),('Nagoya','名古屋','나고야'),('Sapporo','札幌','삿포로'),('Akihabara','秋葉原','아키하바라'),('Asakusa','淺草','아사쿠사'),('Ueno','上野','우에노'),('Iriya','入谷','이리야'),('Kuramae','藏前','구라마에'),('Nihonbashi','日本橋','니혼바시'),('Kamata','蒲田','가마타'),('Gion','祇園','기온'),('Sanjo','三條','산조'),('Gojo','五條','고조'),('Kiyomizu-Gojo','清水五條','기요미즈고조'),('Shijo Omiya','四條大宮','시조오미야'),('Shin-Osaka','新大阪','신오사카'),('Juso','十三','주소'),('Umeda','梅田','우메다'),('Namba','難波','난바')]:AREA[en]=(zh,ko)
for en,zh,ko in [('Chuo','中央區','주오구'),('Taito','台東區','다이토구'),('Arakawa','荒川區','아라카와구'),('Sumida','墨田區','스미다구'),('Minato','港區','미나토구'),('Ota','大田區','오타구'),('Shinjuku','新宿區','신주쿠구'),('Toshima','豐島區','도시마구'),('Higashiyama','東山區','히가시야마구'),('Minami','南區','미나미구'),('Nakagyo','中京區','나카교구'),('Shimogyo','下京區','시모교구'),('Naniwa','浪速區','나니와구'),('Nishi','西區','니시구'),('Fukushima','福島區','후쿠시마구'),('Higashiyodogawa','東淀川區','히가시요도가와구'),('Yodogawa','淀川區','요도가와구'),('Naka','中區','나카구'),('Higashi','東區','히가시구'),('Kita','北區','기타구'),('Hakata','博多區','하카타구'),('Moji','門司區','모지구')]:AREA[en]=(zh,ko)
def soup(t):return BeautifulSoup(t,'html.parser')
def route(l,slug):return ('/' if l=='en' else '/'+l+'/')+'stays/'+slug+'/'
def lists(l):return [f'/en/tokyo/hotels-for-{n}-guests/' for n in (4,6,8)]+['/en/tokyo/apartment-hotels-for-longer-stays/'] if l=='en' else [f'/{l}/tokyo/{n}-guests/' for n in (4,6,8)]+[f'/{l}/tokyo/long-stay-apartment-hotels/']
def file(u):return u.lstrip('/')+'index.html'
def tag(s,name,text=None,**attrs):
 x=s.new_tag(name,attrs=attrs)
 if text is not None:x.string=text
 return x
def breadcrumb(s,l,u):
 for x in s.select('.gsj-v7-breadcrumb'):x.decompose()
 nav=tag(s,'nav',**{'class':'gsj-v7-breadcrumb','aria-label':'Breadcrumb'});nav.append(tag(s,'a',HOME[LANGS.index(l)],href='/'));nav.append(' › '+s.h1.get_text());s.h1.insert_before(nav)
 for x in s.select('script[type="application/ld+json"]'):
  try:d=json.loads(x.string or '')
  except ValueError:continue
  if isinstance(d,dict) and d.get('@type')=='BreadcrumbList':x.decompose()
 d={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':HOME[LANGS.index(l)],'item':BASE+'/'},{'@type':'ListItem','position':2,'name':s.h1.get_text(),'item':BASE+u}]}
 x=tag(s,'script',json.dumps(d,ensure_ascii=False),type='application/ld+json');s.head.append(x)
def build(day,out):
 targets=['index.html','_SYSTEM/partners.html','_SYSTEM/about.html']+[file(u) for l in LANGS for u in lists(l)]+[p.relative_to(R).as_posix() for l in LANGS for p in (R/('stays' if l=='en' else l+'/stays')).glob('*/index.html')]+['sitemap.xml','sitemap-core.xml','sitemap-stays-en.xml','sitemap-stays-ja.xml']
 out.mkdir(parents=True,exist_ok=True); baseline=out/'baseline.zip'
 if not baseline.exists():
  with zipfile.ZipFile(baseline,'w',zipfile.ZIP_DEFLATED) as z:
   for p in targets:z.write(R/p,p)
 with zipfile.ZipFile(baseline) as z:original={p:z.read(p) for p in z.namelist()}
 pages={p:soup(b.decode('utf8')) for p,b in original.items() if p.endswith('.html')}
 output={};counts=[];membership={};links_report={};remnants=[]
 beds=json.loads((R/'assets/gsj-home-beds.json').read_text(encoding='utf8'))['properties']
 titles={u:pages[file(u)].h1.get_text() for l in LANGS for u in lists(l)}
 for l in LANGS:
  for u in lists(l):
   s=pages[file(u)]; membership[u]=set()
   for a in s.select('a[data-stay],a[data-room-link],table a[href]'):
    m=re.search('/stays/([^/?#]+)/',a.get('href',''))
    if m:membership[u].add(m[1])
   breadcrumb(s,l,u)
   labels=['Official source ·','公式出典 ·','官方來源 ·','공식 출처 ·']
   changed=0
   for tr in s.select('tr'):
    cells=tr.find_all('td',recursive=False)
    for a in tr.select('a'):
     if any(x in a.get_text() for x in labels):
      brand=cells[1].get_text(' ',strip=True).split()[0]
      if cells[1].contents:brand=str(cells[1].contents[0]).strip()
      a.string=[brand+' official page',brand+'公式ページ',brand+'官方網頁',brand+' 공식 페이지'][LANGS.index(l)];changed+=1
   if changed:
    note=['Room details checked on the official sites on 2026-09-25.','客室情報は2026/9/25に各公式サイトで確認しました。','客房資訊於2026/9/25依各官方網站確認。','객실 정보는 2026/9/25에 각 공식 사이트에서 확인했습니다.'][LANGS.index(l)]
    if note not in s.get_text():s.select_one('table').insert_before(tag(s,'p',note))
   if l!='en' and u!=lists(l)[3]:
    n=[4,6,8][lists(l).index(u)];m_total=k_total=zero=0
    for c in s.select('article.card'):
     slug=c.select_one('[data-stay]')['data-stay'];rr=[r for r in beds[slug] if r[0]>=n];m=len(rr);k=sum(r[1] is not None and r[1]>=n for r in rr);m_total+=m;k_total+=k;zero+=m==0
     line=([f'{n}人全員がベッドで寝られる客室：{m}室中{k}室',f'{n}人都有床可睡的房型：{m}種中{k}種',f'{n}명 모두 침대에서 잘 수 있는 객실: {m}개 중 {k}개'][LANGS.index(l)-1] if m else ['この人数で泊まれる客室タイプは掲載していません','未刊載可供此人數入住的房型','이 인원이 묵을 수 있는 객실 유형은 게재하지 않았습니다'][LANGS.index(l)-1])
     old=c.select_one('.gsj-beds-card')
     if old:old.string=line
     else:c.select_one('.body').append(tag(s,'p',line,**{'class':'gsj-beds-card'}))
    counts.append({'url':u,'denominator':m_total,'numerator':k_total,'zeroCards':zero,'pass':(m_total,k_total)=={4:(142,114),6:(56,35),8:(16,7)}[n]})
 # Known names are protected across all languages, including neighbor links.
 names=set()
 for p,s in pages.items():
  if '/stays/' in '/'+p:names.update(x.get_text(strip=True) for x in s.select('h1,[data-official-name],#room-type option'))
 names.discard('')
 tokyo=set().union(*(membership[u] for u in lists('en')))
 assert len(tokyo)==26,len(tokyo)
 facts={}
 for p,s in pages.items():
  if '/stays/' not in '/'+p:continue
  l='en' if p.startswith('stays/') else p.split('/')[0];slug=p.split('/')[-2];u=route(l,slug);breadcrumb(s,l,u)
  for x in s.select('link[hreflang]'):x.decompose()
  for ll,code in [('en','en'),('ja','ja'),('zh-tw','zh-Hant'),('ko','ko'),('en','x-default')]:s.head.append(tag(s,'link',rel='alternate',hreflang=code,href=BASE+route(ll,slug)))
  if slug in tokyo:
   uu=[v for v in lists(l) if slug in membership[v]];assert uu,(p,'no matching lists');links_report[u]=uu
   lead=['Compare with other Tokyo rooms: ','東京のほかの客室と比べる：','與東京其他房型比較：','도쿄의 다른 객실과 비교: '][LANGS.index(l)]
   line=tag(s,'p',lead,**{'class':'gsj-v7-compare'})
   for j,v in enumerate(uu):
    if j:line.append(' · ')
    labels=[['for 4 guests','for 6 guests','for 8 guests','for longer stays'],['4人','6人','8人','連泊'],['4人','6人','8人','多晚住宿'],['4명','6명','8명','장기 숙박']][LANGS.index(l)]
    line.append(tag(s,'a',labels[lists(l).index(v)],href=v))
   s.select_one('.hero').append(line)
  nav=s.select_one('.gsj-language-links')
  if nav and nav.contents and isinstance(nav.contents[-1],str):nav.contents[-1].extract()
  if l=='en' and slug in beds:
   areas=[]
   for a in s.select('article.room .metrics'):
    for t in a.select('.pill'):
     m=re.fullmatch(r'([\d.]+) m²',t.get_text(strip=True))
     if m:areas.append(float(m[1]))
   facts[slug]={'count':len(s.select('article.room')),'min':min(areas) if areas else None,'max':max(areas) if areas else None}
  if l in ['zh-tw','ko']:
   s.select_one('meta[name=robots]')['content']='index,follow';idx=0 if l=='zh-tw' else 1
   for node in list(s.body.find_all(string=True)):
    if isinstance(node,(Doctype,Comment)) or any(a.name in ['script','style'] or a.has_attr('data-official-name') or a.has_attr('data-official-quote') for a in node.parents):continue
    t=str(node)
    # Preserve complete postal addresses until a verified full translation is supplied;
    # never partially translate a street as a district (e.g. Nishi -> Nishi ward).
    if node.parent.name=='p' and node.parent.parent and 'hero' in node.parent.parent.get('class',[]) and re.match(r'^\s*\d',t):continue
    if t.strip() in names:continue
    # Names embedded in translated sentences remain unchanged.
    protected={};
    for k,name in enumerate(sorted(names,key=len,reverse=True)):
     if name in t:token='\uE000'+str(k)+'\uE001';protected[token]=name;t=t.replace(name,token)
    for en,(zh,ko) in sorted(AREA.items(),key=lambda kv:-len(kv[0])):t=re.sub(r'(?<![A-Za-z])'+re.escape(en)+r'(?![A-Za-z])',zh if idx==0 else ko,t)
    if node.parent.name=='option' and node.parent.parent.get('id')=='booking-currency':t=re.sub(r'^(JPY|USD|TWD|KRW) — ','',t)
    for token,name in protected.items():t=t.replace(token,name)
    if t!=str(node):node.replace_with(t)
 # About/partners prose with all languages.
 for p in ['_SYSTEM/about.html','_SYSTEM/partners.html']:
  s=pages[p];block=tag(s,'section',**{'class':'gsj-v7-guides'})
  bilingual=bool(re.search('[ぁ-んァ-ン]',s.get_text()))
  for l in (['en','ja'] if bilingual else ['en']):
   para=tag(s,'p','To compare rooms, start with our Tokyo lists by group size: ' if l=='en' else '部屋を比べるなら、東京の人数別の一覧からどうぞ：')
   for j,u in enumerate(lists(l)):
    if j:para.append(', ')
    para.append(tag(s,'a',(['rooms for 4 guests','rooms for 6 guests','rooms for 8 guests','rooms for longer stays'] if l=='en' else ['4人','6人','8人','連泊'])[j],href=u))
   para.append('. The same lists are also available in Japanese, Traditional Chinese and Korean:' if l=='en' else '。英語・繁体字・韓国語の一覧もあります：');block.append(para)
   ul=tag(s,'ul')
   for ll in LANGS:
    if ll==l:continue
    for u in lists(ll):li=tag(s,'li');li.append(tag(s,'a',titles[u],href=u));ul.append(li)
   block.append(ul);block.append(tag(s,'a','See all stays on the home page' if l=='en' else 'トップページで全施設を見る',href='/'))
  anchor=s.find('h1');anchor.insert_after(block)
 s=pages['index.html'];s.h1.string='Apartment hotels for groups and longer stays in Japan';s.h1['data-i18n']='lead';lead=s.select_one('p.lead');lead.string='Stay together. Stay longer.';lead.attrs.pop('data-i18n',None)
 for a in s.select('#all-stays-directory a'):
  if a.get_text(strip=True)=='日本語':
   prev=a.previous_sibling
   if isinstance(prev,str) and prev.strip()=='·':prev.extract()
   a.decompose()
 block=tag(s,'section',**{'class':'gsj-wrap','id':'gsj-v7-tokyo'});block.append(tag(s,'h2','Tokyo by group size',**{'data-v7-heading':''}))
 for l in LANGS:
  ul=tag(s,'ul',lang='zh-Hant' if l=='zh-tw' else l)
  for u in lists(l):li=tag(s,'li');li.append(tag(s,'a',titles[u],href=u));ul.append(li)
  block.append(ul)
 s.select_one('#all-stays-directory').insert_before(block)
 # Change original card generator, keeping click handlers untouched.
 sc=next(x for x in s.select('script') if 'function render()' in (x.string or ''));t=sc.string
 t=re.sub(r'<span class="card-match">.*?</span>','',t)
 t=re.sub(r'<span class="availability-note">.*?</span>','',t)
 t=t.replace("${jaMode?'選択日程の空室・最終料金':'Live availability for your dates'}",'')
 t=t.replace("<span>'+(jaMode?'現在は空室と最終料金をTrip.comで確認します。':'Availability and final prices are confirmed live on Trip.com.')+'</span>",'')
 t=t.replace('<span class="fact">${s.size}</span><span class="fact">${s.feature}</span>','${v7Facts(s.id)}')
 prefix='const v7RoomFacts='+json.dumps(facts,ensure_ascii=False)+';\n'+'''function v7Facts(id){const f=v7RoomFacts[id];if(!f)return '';const n=f.count;const count=lang==='ja'?'客室タイプ'+n:lang==='zh-TW'?n+'種房型':lang==='ko'?'객실 유형 '+n+'개':n+' room types';const area=f.min===null?'':f.min===f.max?f.min+' m²':f.min+(lang==='ja'?'〜':'–')+f.max+' m²';return (area?'<span class="fact">'+area+'</span>':'')+'<span class="fact">'+count+'</span>';}
'''
 sc.string=prefix+t
 for old_notice in s.select('#resultsStatus span'):old_notice.decompose()
 notice=tag(s,'p','Live availability and final prices are shown on Trip.com.',id='gsj-v7-availability');s.select_one('#grid').insert_before(notice)
 js="""(()=>{const words={en:['Tokyo by group size','Live availability and final prices are shown on Trip.com.'],ja:['東京・人数別','空室と最終料金はTrip.comで確認できます。'],'zh-TW':['東京・依人數','即時空房與最終價格請在Trip.com確認。'],ko:['도쿄 · 인원별','실시간 빈방과 최종 요금은 Trip.com에서 확인하세요.']};function update(){const t=words[document.querySelector('#lang')?.value]||words.en;document.querySelector('[data-v7-heading]').textContent=t[0];document.querySelector('#gsj-v7-availability').textContent=t[1];}addEventListener('gsj-language',update);update();})();"""
 s.body.append(tag(s,'script',js))
 # Preserve original newline style; no changes to any other generated file.
 for p,s in pages.items():
  text=str(s);nl='\r\n' if b'\r\n' in original[p] else '\n';output[p]=text.replace('\r\n','\n').replace('\n',nl).encode('utf8')
 import xml.etree.ElementTree as E
 ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
 changed={BASE+'/'}|{BASE+u for l in LANGS for u in lists(l)}|{BASE+'/_SYSTEM/'+x+'.html' for x in ['partners','about']}|{BASE+route(l,slug) for l in ['en','ja'] for slug in tokyo}
 for p in ['sitemap-core.xml','sitemap-stays-en.xml','sitemap-stays-ja.xml']:
  t=original[p].decode('utf8')
  def upd(m):
   chunk=m[0];url=re.search(r'<loc>(.*?)</loc>',chunk)[1]
   if url not in changed:return chunk
   chunk=re.sub(r'<lastmod>.*?</lastmod>','',chunk);return chunk.replace('</url>',f'<lastmod>{day}</lastmod></url>')
  output[p]=re.sub(r'<url>.*?</url>',upd,t,flags=re.S).encode('utf8')
 enurls=[x.find(ns+'loc').text for x in E.fromstring(original['sitemap-stays-en.xml'])]
 for l in ['zh-tw','ko']:
  output['sitemap-stays-'+l+'.xml']=('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+u.replace('/stays/','/'+l+'/stays/')+'</loc><lastmod>'+day+'</lastmod></url>' for u in enurls)+'</urlset>').encode()
 output['sitemap.xml']=original['sitemap.xml'].replace(b'</sitemapindex>',(''.join('<sitemap><loc>'+BASE+'/sitemap-stays-'+l+'.xml</loc></sitemap>' for l in ['zh-tw','ko'])+'</sitemapindex>').encode())
 for p,b in output.items():(R/p).write_bytes(b)
 (out/'card-counts.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2),encoding='utf8')
 (out/'tokyo-links.json').write_text(json.dumps(links_report,ensure_ascii=False,indent=2),encoding='utf8')
 (out/'area-translations.json').write_text(json.dumps(AREA,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'written':len(output),'tokyoProperties':len(tokyo),'cardCounts':counts},ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--date',default=datetime.now(timezone(timedelta(hours=9))).date().isoformat());a.add_argument('--review-dir',default=str(R.parent/'gsj-v7-20261012'));x=a.parse_args();build(x.date,Path(x.review_dir))