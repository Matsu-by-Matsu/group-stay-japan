import json,re,html,statistics,subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from room_model import build,ROOT
from v33_localization import area_label, bed_text, clean_quote, localize, finalize, size_comparison
P,CFG=build();ORIGIN='https://groupstayjapan.synthx.jp';BY={p['id']:p for p in P};ACTIVE=[p for p in P if not p['excluded']];ALL=[(p,r) for p in ACTIVE for r in p['rooms'] if not r['bundle']];esc=lambda x:html.escape(str(x if x is not None else '—'),quote=True)
def route(p,lang='en'):return ('/ja' if lang=='ja' else '')+'/stays/'+p['id']+'/'
def source(p):return f'<a href="{esc(p["source"])}" target="_blank" rel="noopener">Official source · {p["checked"]}</a>'
def state(v,ja=False):return ('あり' if ja else 'Yes') if v is True else ('非対応' if ja else 'Not supported') if v is False else ('未確認' if ja else 'Unverified')
def count(v):return esc(v) if v is not None else '—'
def rank(r,group):
 if r['areaPerPerson'] is None:return None
 vals=[x['areaPerPerson'] for x in group if x['capacity']==r['capacity'] and x['areaPerPerson'] is not None and not x['bundle']]
 return (1+sum(v>r['areaPerPerson'] for v in vals),len(vals)) if vals else None

def example(context='list'):
 x=CFG['example'];g=x['guests'];a=x['apartmentNightly']/g;lo,hi=x['businessSingleNightly'];ns=[1,4,10,20] if context=='hub' else [1,4,10]
 title='Apartment hotel vs. business hotel for groups' if context=='hub' else 'Why an apartment hotel for your group?'
 copy='Most hotel rooms in Japan are designed for one or two people, so a group of six often ends up booking three or more separate rooms. An apartment hotel keeps everyone in one unit, often with a kitchen and a washing machine. Divide the room price by the number of guests, and the cost per person can be lower than booking separate business hotel rooms.'
 if context=='hub':copy='Business hotels can suit you better if you want a staffed front desk and daily cleaning. For groups who want to stay together, cook, or do laundry during a longer stay, an apartment hotel is often the better fit. With a kitchen and an in-room washing machine, you can also save on eating out and coin laundry, and those savings grow the longer you stay.'
 yen=lambda n:'¥'+format(round(n),',')
 rows=''.join(f'<tr><td>{n}</td><td>{yen(a*n)}</td><td>{yen(lo*n)}–{yen(hi*n)}</td><td>{yen((lo-a)*n)}–{yen((hi-a)*n)}</td><td>{yen((lo-a)*n*g)}–{yen((hi-a)*n*g)}</td></tr>' for n in ns)
 return f'<section><h2>{title}</h2>{hotel_comparison() if context=="hub" else ""}<p>{copy}</p><h3>Example calculation</h3><p>One unit for 6 guests at ¥60,000 per night, compared with one business hotel single room per guest at ¥12,000–14,000 per night.</p><div class="table-scroll"><table><thead><tr><th>Nights</th><th>Apartment hotel, per person</th><th>Business hotel, per person</th><th>Difference per person</th><th>Difference for the group</th></tr></thead><tbody>{rows}</tbody></table></div><p>This is an example calculation. Actual prices vary by date, season and property.</p></section>'

def hotel_comparison():
 rows=[('Rooms for 6 guests','Usually one unit','At least 3 twin rooms'),('Shared space','Living and dining space for the group','Separate rooms'),('Kitchen','Often in the unit','Rarely in the room'),('Laundry','Often an in-room washing machine','Shared coin laundry at some hotels'),('Front desk','Often limited hours or self check-in','Usually staffed 24 hours'),('Cleaning during your stay','Often every few days or on request','Often daily')]
 return '<div class="table-scroll"><table><thead><tr><th>Feature</th><th>Apartment hotel</th><th>Business hotel</th></tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'

def comparison(items,lang='en',page='list',minimum=1):
 ja=lang=='ja';heads=['施設・客室','ブランド／エリア','定員','ベッド構成','面積／1人あたり','寝室／浴室／トイレ','室内洗濯機／キッチン','連泊適性','出典'] if ja else ['Property / room','Brand / area','Capacity','Sleeping arrangement','Area / per guest','Bedrooms / baths / toilets','In-room washer / kitchen','Stay readiness','Source']
 rows=[]
 for p,r in items:
  if r['level']<minimum:continue
  href=route(p,lang)+'?room='+r['key']+'&from='+page
  cap=str(r['capacity'])+(' adults' if 'adults' in r['capacityBasis'] else '')
  if r['childAllowance'] is not None:cap+='; children allowance '+str(r['childAllowance'])+' separately'
  area=(str(r['area'])+' m²') if r['area'] is not None else esc(r['areaText'] or '—')
  rows.append(f'<tr data-stay-level="{r["level"]}" data-property="{p["id"]}"><td><a data-room-link href="{esc(href)}">{esc(p["name"])}</a><br><span data-official-name>{esc(r["name"])}</span></td><td>{esc(p["brand"])}<br>{esc(area_label(p["areaKey"],lang))}</td><td>{esc(cap)}</td><td>{esc(bed_text(r["beds"],lang) or "—")}{sleeping_numbers(r)}</td><td>{area}<br>{count(r["areaPerPerson"])} m² / guest</td><td>{count(r["bedrooms"])} / {count(r["bathrooms"])} / {count(r["toilets"])}</td><td>{state(r["washer"],ja)} / {state(r["kitchen"],ja)}</td><td>{CFG["levels"][r["level"]-1]["label"]}</td><td>{source(p)}</td></tr>')
 return '<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in heads)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'

def sleeping_numbers(r):
 return ('<br>Bed sleepers: '+count(r['bedSleepers'])+' · Sofa beds: '+count(r['sofaBeds'])+' · Futons: '+count(r['futons'])) if r['bedSleepers'] is not None else ''

def cleaning(items):
 out=[]
 for p in items:
  c=p['policy']['cleaningLinen'];conflict=p['id'] in CFG['cleaningConflictAllowed']
  if c['status']!='official_statement_found' and not conflict:continue
  seen=set()
  for e in c['evidence']:
   t=clean_quote(BeautifulSoup(e['text'],'html.parser').get_text(' ',strip=True));t=re.sub(r'\s+',' ',t)
   if t in seen:continue
   seen.add(t);freq='';start='';fee=''
   if 'every 7 days' in t:freq='Every 7 days after the first service'
   elif 'every two days' in t:freq='Every two days; daily towels / vacuuming separately'
   elif re.search(r'3\s*日毎|3日に1回',t):freq='Every 3 days'
   if 'on the 4th day' in t or re.search(r'4\s*日目',t):start='Day 4'
   elif 'starting from the third day' in t:start='Third day (official wording: excluding check-in day)'
   if '7 nights or more' in t:start+='; stays of 7+ nights only'
   if '無料' in t:fee='Scheduled service: free'
   if re.search(r'additional charge|有料',t):fee+=('; ' if fee else '')+'Additional service: paid'
   out.append(f'<tr><td>{esc(p["name"])}'+(' — Official information conflict' if conflict else '')+f'</td><td>{esc(freq)}</td><td>{esc(start)}</td><td>{esc(fee)}</td><td><details><summary>Official wording</summary><blockquote data-official-quote>{esc(t)}</blockquote></details><a href="{esc(e["sourceUrl"])}">Source</a> · {e["retrievedAt"][:10]}</td></tr>')
 return '<section><h2>Cleaning during longer stays — official policies</h2><p>Blank cells mean the detail was not confirmed. Conflicting official policies are shown separately.</p><div class="table-scroll"><table><thead><tr><th>Property</th><th>Frequency</th><th>First service / eligibility</th><th>Free / paid</th><th>Official statement</th></tr></thead><tbody>'+''.join(out)+'</tbody></table></div></section>'

def criteria():
 return '<section><h2>How stay readiness is checked</h2><ul>'+''.join(f'<li>{x["label"]}: '+(', '.join(x['requires']) or 'published room specifications')+'</li>' for x in CFG['levels'])+'</ul><p>Kitchen means the official room description explicitly lists a kitchen. Stove type and burner count are displayed only when confirmed. A missing condition is unverified, not proof of absence. For longer stays, confirm cleaning and linen changes, laundry, kitchen equipment, minimum / maximum nights and the booking conditions. Extended-stay readiness requires an explicit long-stay plan or permission for at least '+str(CFG['extendedStayNights'])+' nights.</p></section>'

def page_shell(title,desc,body,url,lang='en',alts=None,data=None):
 alts=alts or {'en':url,'x-default':url};links=''.join(f'<link rel="alternate" hreflang="{k}" href="{ORIGIN+v}">' for k,v in alts.items())
 analytics="if(location.hostname==='groupstayjapan.synthx.jp'){window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-GVQ24M4R7R');const s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id=G-GVQ24M4R7R';document.head.appendChild(s)}"
 ld={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'GROUP STAY JAPAN','item':ORIGIN+'/'},{'@type':'ListItem','position':2,'name':title,'item':ORIGIN+url}]}
 return f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{ORIGIN+url}">{links}<link rel="stylesheet" href="/assets/gsj-rooms.css?v=20260926ui1"><link rel="stylesheet" href="/assets/gsj-ui.css?v=20260926ui1"><script>{analytics}</script><script src="/assets/gsj-attribution.js"></script><script type="application/ld+json">{json.dumps(ld,ensure_ascii=False).replace("<",chr(92)+"u003c")}</script></head><body><header><a href="/">GROUP STAY JAPAN</a></header><main>{body}</main><footer><a href="/">GROUP STAY JAPAN</a> · <a href="/_SYSTEM/about.html">About</a><p>Affiliate links: we may receive a commission when you book.</p></footer><script id="gsj-page-data" type="application/json">{json.dumps(data or {},ensure_ascii=False).replace("<",chr(92)+"u003c")}</script><script src="/assets/gsj-rooms.js?v=20260926ui1" defer></script><script src="/assets/gsj-ui.js?v=20260926ui1" defer></script></body></html>'

def property_page(p,lang):
 ja=lang=='ja';url=route(p,lang);title=p['name']+' · '+p['place']+' | GROUP STAY JAPAN';desc=f'{p["name"]}: compare official room capacities, sleeping arrangements, kitchen and laundry facilities in {p["place"]}.'
 body=f'<section class="hero"><p>{esc(p["brand"])} · {esc(p["place"])}</p><h1>{esc(p["name"])}</h1><p>{esc(p["address"])}</p><nav><a href="{route(p)}">English</a> · <a href="{route(p,"ja")}">日本語</a></nav></section>'
 if p['excluded']:body+='<p class="warning">公式サイトで掲載を確認できません（2026年9月25日時点）<br>This property could not be confirmed on the official website as of September 25, 2026. It is excluded from comparisons and recommendations.</p>'
 photos=p['photos'];body+='<div class="gallery">'+''.join(f'<a href="{esc(u.replace("../","/",1))}"><img src="{esc(u.replace("../","/",1))}" alt="{esc(p["name"])} photo {i+1}" loading="{"eager" if i==0 else "lazy"}"></a>' for i,u in enumerate(photos))+'</div>'
 body+=f'<p>{"公式客室の最大定員" if ja else "Maximum official room capacity"}: <strong>{count(p["max"])}</strong> · {source(p)}</p>'
 for r in p['rooms']:
  a=r['areaPerPerson'];brand=rank(r,[v for h,v in ALL if h['brand']==p['brand']]);area=rank(r,[v for h,v in ALL if h['areaKey']==p['areaKey'] and p['areaKey']!='unclassified']);peers=[statistics.mean([v['area'] for v in h['rooms'] if v['capacity']==r['capacity'] and v['area'] is not None and not v['bundle']]) for h in ACTIVE if any(v['capacity']==r['capacity'] and v['area'] is not None and not v['bundle'] for v in h['rooms'])]
  metrics=[f'{r["capacity"]} '+('adults' if 'adults' in r['capacityBasis'] else 'guests'),(f'{r["area"]} m²' if r['area'] else r['areaText'] or 'Area unverified')]
  if a is not None:metrics.append(f'{a} m² / guest')
  for k,label in [('bedrooms','bedrooms'),('bathrooms','bathrooms'),('toilets','toilets')]:
   if r[k] is not None:metrics.append(f'{r[k]} {label[:-1] if r[k]==1 else label}')
  body+=f'<article class="room" id="room-{r["key"]}"><h2 data-official-name>{esc(r["name"])}</h2><div class="metrics">'+''.join(f'<span class="pill">{esc(v)}</span>' for v in metrics)+'</div>'
  body+=f'<p>{esc(bed_text(r["beds"],lang) or "Sleeping arrangement unverified")}</p>{sleeping_numbers(r)}'
  if r['childAllowance'] is not None:body+=f'<p>Adult capacity excludes a separate official allowance of {r["childAllowance"]} children. Confirm ages and bed-sharing conditions with the property.</p>'
  if r['bundle']:body+=f'<p class="warning">{esc(r["bundleNote"])}</p>'
  body+=f'<p>{CFG["levels"][r["level"]-1]["label"]} · In-room washer: {state(r["washer"],ja)} · Kitchen: {state(r["kitchen"],ja)}</p>'
  equipment=[]
  for k,label in [('hob','Stove / IH'),('hobBurners','Burners'),('dryer','Drying facility'),('microwave','Microwave'),('refrigerator','Refrigerator'),('cookware','Cookware'),('tableware','Tableware')]:
   if r[k] is not None:equipment.append(label+': '+(state(r[k],ja) if isinstance(r[k],bool) else str(r[k])))
  body+='<p>'+esc(' · '.join(equipment))+'</p>'
  body+='<details><summary>Readiness evidence</summary><ul>'+''.join(f'<li>{CFG["levels"][x["level"]-1]["label"]}: { {'supported':'Confirmed','not_supported':'Not supported','unverified':'Unverified'}[x['state']] }; '+', '.join(f"{ {'washer':'In-room washer','kitchen':'Kitchen','cleaning':'Cleaning policy','extended':'20+ night policy'}[k]}: { {'yes':'confirmed','no':'not supported','unknown':'unverified'}[v]}" for k,v in x['conditions'].items())+'</li>' for x in r['levels'])+'</ul>'+source(p)+'</details>'
  if a is not None:body+=size_comparison(p,r,brand,area,peers,lang)
  body+='</article>'
 if p['rooms']:
  body+=cleaning([p])
  options=''.join(f'<option data-official-name value="{r["key"]}">{esc(r["name"])}</option>' for r in p['rooms'] if not r['bundle'])
  body+=f'<section class="booking"><h2>{"日程・客室を選ぶ" if ja else "Choose a room and dates"}</h2><form id="booking"><label>Room type <select id="room-type">{options}</select></label><label>Check-in <input type="date" id="checkIn" required></label><label>Check-out <input type="date" id="checkOut" required></label><label>Rooms <input id="room-count" type="number" min="1" value="1"></label><label>Guests <input id="guests" type="number" min="1" max="{p["max"]}" value="4" required></label><label>Nights <select id="stay-duration"><option value="">Custom</option><option value="2">2</option><option value="5">5</option><option value="10">10</option></select></label><p id="booking-error" class="error" role="status"></p><button type="submit">Check availability on Trip.com</button></form><p>Confirm the selected room, dates, guests, room count and final conditions on Trip.com. This page does not display live prices or availability.</p><a href="{esc(p["partner"])}" rel="sponsored noopener" target="_blank" data-affiliate-link>Trip.com</a></section>'
 neighbors=[h for h in ACTIVE if h['id']!=p['id'] and h['areaKey']==p['areaKey'] and p['areaKey']!='unclassified'][:5] if not p['excluded'] else []
 if neighbors:
  body+='<section><h2>Other stays in '+esc(area_label(p['areaKey'],lang))+'</h2><div class="neighbors">'
  for h in neighbors:
   r=next((x for x in h['rooms'] if x['capacity'] and x['capacity']>=4 and not x['bundle']),None)
   if r:body+=f'<article><a href="{route(h,lang)}">{esc(h["name"])}</a><p><span data-official-name>{esc(r["name"])}</span> · {r["capacity"]} guests · {count(r["area"])} m² · {count(r["areaPerPerson"])} m² / guest · {CFG["levels"][r["level"]-1]["label"]}</p></article>'
  body+='</div></section>'
 if ja:
  title=p['name']+' · '+p['place']+'の宿泊・客室情報 | GROUP STAY JAPAN';desc=p['name']+'の公式客室情報。定員・寝具構成・キッチン・洗濯設備・連泊中の清掃ルールを客室別に比較できます。'
 return page_shell(title,desc,body,url,lang,{'en':route(p),'ja':route(p,'ja'),'x-default':route(p)},dict(id=p['id'],lang=lang,partner=p['partner'],pageType='property',bookingParameters=CFG['booking']['additionalParameters'],rooms=[{k:r[k] for k in ['key','name','capacity','level']} for r in p['rooms'] if not r['bundle']]))

def enhance(path,content,title=None,h1=None,desc=None):
 fp=ROOT/path;s=BeautifulSoup(fp.read_text(encoding='utf8'),'html.parser')
 for el in s.select('.gsj-v31'):el.decompose()
 if str(path).startswith('en/tokyo/'):
  for el in s.select('section.content,section.guide,section.editorial,section.faq'):el.decompose()
 if title:
  s.title.string=title
  for tag in s.find_all('meta',attrs={'property':'og:title'}):tag['content']=title
  for tag in s.find_all('meta',attrs={'name':'twitter:title'}):tag['content']=title
 if h1 and s.h1:s.h1.clear();s.h1.append(h1)
 if str(path)=='index.html':
  lead=s.select_one('.hero .lead')
  if lead:
   lead.attrs.pop('data-t',None);lead.clear();lead.append('Apartment hotels for groups and longer stays in Japan')
 if desc:
  m=s.find('meta',attrs={'name':'description'})
  if m:m['content']=desc
  for tag in s.find_all('meta',attrs={'property':'og:description'}):tag['content']=desc
 if not s.find('link',href='/assets/gsj-rooms.css'):t=s.new_tag('link',rel='stylesheet',href='/assets/gsj-rooms.css');s.head.append(t)
 if not s.find('script',src='/assets/gsj-rooms.js'):t=s.new_tag('script',src='/assets/gsj-rooms.js',defer=True);s.body.append(t)
 section=s.new_tag('section',attrs={'class':'gsj-v31 gsj-wrap'});section.append(BeautifulSoup(content,'html.parser'))
 hero=s.select_one('.search-stage') if str(path)=='index.html' else s.select_one('.hero')
 if hero:hero.insert_after(section)
 else:s.main.insert(0,section)
 fp.write_text(str(s),encoding='utf8')

for p in P:
 for lang in ['en','ja']:
  file=ROOT/route(p,lang).lstrip('/')/'index.html';file.write_text(property_page(p,lang),encoding='utf8')

TOKYO=[(p,r) for p,r in ALL if 'Tokyo' in p['address'] or '東京' in p['address']]
titles={4:('Tokyo Apartment Hotels for 4 | Kitchen & Washing Machine','Tokyo Apartment Hotels for 4 Guests'),6:('Tokyo Apartment for 6 Guests | Group Stays & Longer Stays','Tokyo Apartments for 6 Guests'),8:('Tokyo Group Accommodation for 8 | Two Families, Longer Stays','Tokyo Group Accommodation for 8 Guests')}
for n in [4,6,8]:
 items=[(p,r) for p,r in TOKYO if r['capacity'] and r['capacity']>=n];num=len(items);fac=len({p['id'] for p,r in items});week=sum(r['level']>=2 for p,r in items);long=sum(r['level']>=3 for p,r in items)
 intro=f'<h2>Compare exact rooms for {n} guests</h2><p>{num} room types across {fac} Tokyo properties meet this capacity. {week} have official in-room laundry and a kitchen; {long} also have a published cleaning policy.</p>'
 selector='<label>Stay readiness <select data-level-filter><option value="1">All rooms / 2–4 nights</option><option value="2">5–9 nights</option><option value="3">10–19 nights</option><option value="4">20+ nights</option></select></label><p>Visible room types: <span data-filter-count>'+str(num)+'</span></p>'
 extra=f'<h2>Business hotel or apartment hotel for {n} guests?</h2><p>In a typical business hotel, {n} guests need at least {n//2} twin rooms. An apartment hotel lets your group stay together in one unit, and splitting the price by {n} guests can bring the cost per person below that of separate rooms.</p>'+('<section><h3>'+example().split('<h3>',1)[1])
 enhance(f'en/tokyo/hotels-for-{n}-guests/index.html',intro+selector+comparison(items,page=f'list_{n}')+extra,*titles[n],desc=f'Compare {num} official Tokyo room types for {n} guests, with room-level kitchen, laundry and longer-stay conditions.')

before=BeautifulSoup((ROOT/'review/urls-before.xml').read_text(encoding='utf8'),'xml');URLS=[x.text for x in before.find_all('loc')]
for url in URLS:
 if 'long' not in url or '/stays/' in url:continue
 path=url.removeprefix(ORIGIN).strip('/')+'/index.html';lang='ja' if '/ja/' in url else 'zh-Hant' if '/zh-tw/' in url else 'ko' if '/ko/' in url else 'en'
 items=TOKYO;ext=any(r['level']>=4 for p,r in items);body=criteria()
 for level,label in [(2,'5–9 nights'),(3,'10+ nights')]+([(4,'20+ nights')] if ext else []):body+='<section><h2>'+label+'</h2>'+comparison(items,lang,page='long_stay_hub',minimum=level)+'</section>'
 body+=cleaning(ACTIVE)
 if lang=='en':body=example('hub')+body
 enhance(path,body,title='Tokyo Extended Stay Apartment Hotels | Long Stays with Washer' if lang=='en' else None,h1=('Tokyo Apartment Hotels for Longer Stays: '+('5, 10 and 20+ Nights' if ext else '5 to 10+ Nights')) if lang=='en' else None)

home=ROOT/'index.html';home_text=home.read_text(encoding='utf8');marker='/* gsj-excluded-comparisons */';exclusion='stays.push(...(window.GSJ_EXTRA_STAYS||[]));';patch=marker+'for(let i=stays.length-1;i>=0;i--)if('+json.dumps(CFG['excludedProperties'])+'.includes(stays[i].id))stays.splice(i,1);';home_text=home_text if marker in home_text else home_text.replace(exclusion,exclusion+patch);s=BeautifulSoup(home_text,'html.parser')
for k in ['en','x-default']:
 if not s.find('link',attrs={'hreflang':k}):s.head.append(s.new_tag('link',rel='alternate',hreflang=k,href=ORIGIN+'/'))
# Keep all old directory destinations, grouped by published administrative area.
directory=s.find(id='all-stays-directory')
if directory:
 directory.clear();directory.append(BeautifulSoup('<h2>Stays by area</h2>'+''.join('<details><summary>'+esc(area_label(a,'en'))+'</summary><ul>'+''.join(f'<li><a href="{route(p)}">{esc(p["name"])}</a> · <a href="{route(p,"ja")}">日本語</a></li>' for p in P if p['areaKey']==a)+'</ul></details>' for a in sorted({p['areaKey'] for p in ACTIVE if p['areaKey']!='unclassified'})),'html.parser'))
home.write_text(str(s),encoding='utf8')
nav='<nav><h2>Find your group stay</h2>'+''.join(f'<a class="pill" href="/en/tokyo/hotels-for-{n}-guests/">{n} guests</a>' for n in [4,6,8])+''.join(f'<a class="pill" href="/en/tokyo/apartment-hotels-for-longer-stays/?nights={n}">{label}</a>' for n,label in [(2,'2–4 nights'),(5,'5–9 nights'),(10,'10+ nights')])+'</nav><p>Apartment hotels for groups and longer stays in Japan</p>'
enhance('index.html',nav+example('home'),'Group Stay Japan | Apartment Hotels for Groups & Longer Stays','Stay together. Stay longer.','Apartment hotels for groups and longer stays in Japan. Compare official room capacities, kitchens, laundry and cleaning policies.')

# Same set of 181 page URLs; sitemap XML files are infrastructure, not new content pages.
parts={'sitemap-core.xml':[u for u in URLS if '/stays/' not in u],'sitemap-stays-en.xml':[u for u in URLS if '/stays/' in u and '/ja/stays/' not in u],'sitemap-stays-ja.xml':[u for u in URLS if '/ja/stays/' in u]}
for name,urls in parts.items():(ROOT/name).write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+u+'</loc></url>' for u in urls)+'</urlset>',encoding='utf8')
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<sitemap><loc>'+ORIGIN+'/'+n+'</loc></sitemap>' for n in parts)+'</sitemapindex>',encoding='utf8')
(ROOT/'data/room-model.json').write_text(json.dumps(P,ensure_ascii=False,indent=2),encoding='utf8')
changes=[{'id':p['id'],'before':p['beforeMax'],'after':p['max'],'source':p['source']} for p in P if p['max']!=p['beforeMax']]
(ROOT/'review/capacity-changes.json').write_text(json.dumps(changes,indent=2),encoding='utf8')
stats=[]
for n in [0,4,6,8]:
 for rule in CFG['levels']:
  rows=[(p,r) for p,r in ALL if (r['capacity'] or 0)>=n and r['level']==rule['level']]
  stats.append({'capacityAtLeast':n,'highestLevel':rule['level'],'properties':len({p['id'] for p,r in rows}),'roomTypes':len(rows)})
(ROOT/'review/level-distribution.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
print('Built 162 property pages, 3 English comparisons, 4 longer-stay hubs, home and split sitemaps. Capacity changes:',len(changes))


finalize(ROOT,P,URLS,example,comparison,criteria,cleaning,TOKYO,enhance)
