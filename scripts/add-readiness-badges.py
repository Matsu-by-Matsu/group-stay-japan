"""Display existing readiness results. Never evaluate or infer room eligibility."""
import json,sys
from pathlib import Path
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]) if len(sys.argv)>1 else R/'data/room-model.json'
properties=json.loads(source.read_text(encoding='utf8'));labels={
'en':['Short stay · 2–4 nights','Week-ready · 5–9 nights','Long-stay ready · 10–19 nights','Extended stay · 20+ nights'],
'ja':['短期滞在（2〜4泊）','5〜9泊向け','10〜19泊向け','20泊以上向け'],
'zh-TW':['短期住宿（2至4晚）','適合5至9晚','適合10至19晚','適合20晚以上'],
'ko':['단기 숙박(2~4박)','5~9박 적합','10~19박 적합','20박 이상 적합']}
css='/assets/gsj-readiness.css?v=20260926';js='/assets/gsj-readiness.js?v=20260926'
def badge(s,level,lang):
 b=s.new_tag('span',attrs={'class':f'gsj-stay-badge gsj-stay-level-{level}','data-readiness-level':str(level)});b.string=labels[lang][level-1];return b
def assets(s):
 if not s.find('link',href=css):s.head.append(s.new_tag('link',rel='stylesheet',href=css))
 if not s.find('script',src=js):s.body.append(s.new_tag('script',src=js,defer=True))
summary={};changed=[]
for p in properties:
 for lang,prefix in [('en',''),('ja','ja/')]:
  f=R/(prefix+'stays/'+p['id']+'/index.html');s=BeautifulSoup(f.read_text(encoding='utf8'),'html.parser')
  if p['excluded']:continue
  rooms=p['rooms'];levels={str(r['key']):r['level'] for r in rooms}
  # Cross-check with the already-published booking data, without recalculation.
  data=json.loads(s.select_one('#gsj-page-data').string)
  assert all(levels[r['key']]==r['level'] for r in data['rooms'])
  for a in s.select('article.room'):
   key=a['id'].removeprefix('room-');level=levels[key]
   for old in a.select('.gsj-stay-badge'):old.decompose()
   a.insert(0,badge(s,level,lang))
  highest=max(levels.values(),default=1);count=sum(v==highest for v in levels.values());total=len(rooms);summary[p['id']]=highest
  if highest==1:text='連泊適性：短期滞在向け（2〜4泊）' if lang=='ja' else 'Long-stay readiness: short stays (2–4 nights)'
  else:
   period={2:'5–9',3:'10–19',4:'20+'}[highest]
   text=(f'連泊適性：最長{period.replace("–","〜").replace("20+","20泊以上")}'+('泊向け' if highest<4 else '向け')+f'（{total}室中{count}室）') if lang=='ja' else f'Long-stay readiness: up to {period} nights ({count} of {total} room types)'
  for old in s.select('.gsj-readiness-summary'):old.decompose()
  row=s.new_tag('p',attrs={'class':f'gsj-readiness-summary gsj-stay-level-{highest}'});row.string=text;s.h1.insert_after(row);assets(s);f.write_text(str(s),encoding='utf8');changed.append(f.relative_to(R).as_posix())
filters={'en':['All','5+ nights','10+ nights'],'ja':['すべて','5泊以上','10泊以上'],'zh-TW':['全部','5晚以上','10晚以上'],'ko':['전체','5박 이상','10박 이상']}
paths=[('en',f'en/tokyo/hotels-for-{n}-guests/index.html') for n in [4,6,8]]+[('en','en/tokyo/apartment-hotels-for-longer-stays/index.html')]+[(lang,folder+'/tokyo/long-stay-apartment-hotels/index.html') for lang,folder in [('ja','ja'),('zh-TW','zh-tw'),('ko','ko')]]
for lang,path in paths:
 f=R/path;s=BeautifulSoup(f.read_text(encoding='utf8'),'html.parser')
 for sel in s.select('[data-level-filter]'):
  label=sel.find_parent('label');(label or sel).decompose()
 for count in s.select('[data-filter-count]'):
  parent=count.find_parent('p');(parent or count).decompose()
 for table in s.select('table'):
  rows=table.select('tr[data-stay-level]')
  if not rows:continue
  for row in rows:
   cell=row.find_all('td')[7];cell.clear();cell.append(badge(s,int(row['data-stay-level']),lang))
  scroller=table.find_parent('div',class_='table-scroll');wrapper=s.new_tag('div',attrs={'class':'gsj-readiness-table'});scroller.wrap(wrapper)
  bar=s.new_tag('div',attrs={'class':'gsj-readiness-filters','role':'group','aria-label':{'en':'Stay length','ja':'泊数で絞り込み','zh-TW':'依晚數篩選','ko':'숙박일 수 필터'}[lang]})
  for level,label in zip([1,2,3],filters[lang]):
   b=s.new_tag('button',type='button',attrs={'data-readiness-filter':str(level),'aria-pressed':str(level==1).lower()});b.string=label;bar.append(b)
  wrapper.insert(0,bar)
 assets(s);f.write_text(str(s),encoding='utf8');changed.append(path)
f=R/'index.html';s=BeautifulSoup(f.read_text(encoding='utf8'),'html.parser');assets(s);f.write_text(str(s),encoding='utf8');changed.append('index.html')
# Public display levels only; no source evidence or personal data.
(R/'assets/gsj-readiness-levels.json').write_text(json.dumps({'labels':labels,'properties':summary},ensure_ascii=False),encoding='utf8')
print('Added existing-result badges to',len(changed),'pages;',len(summary),'active properties. Excluded properties untouched.')
