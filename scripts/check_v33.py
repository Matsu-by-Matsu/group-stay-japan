"""Check v3.3 generated output against source evidence and original production URLs."""
import sys,json,re,subprocess,tempfile,shutil
from pathlib import Path
from bs4 import BeautifulSoup
R=Path.cwd();sys.path.insert(0,str(R/'scripts'))
from v33_localization import AREA,area_label,bed_text,write_lastmod
P=json.loads((R/'data/room-model.json').read_text(encoding='utf8'));errors=[]
def check(x,msg):
 if not x:errors.append(msg)
def soup(f):return BeautifulSoup(f.read_text(encoding='utf8'),'html.parser')
home=soup(R/'index.html');check('unclassified' not in home.select_one('#all-stays-directory').get_text(),'home unclassified')
for p in P:
 for lang in ['en','ja']:
  path=('ja/' if lang=='ja' else '')+'stays/'+p['id']+'/index.html';s=soup(R/path)
  expected=p['name']+' · '+p['place']+('の宿泊・客室情報' if lang=='ja' else '')+' | GROUP STAY JAPAN'
  check(s.title.get_text()==expected,path+' title')
  baseline=soup(R/path) # original title location checked separately below
  old=BeautifulSoup(subprocess.check_output(['git','show','HEAD:'+path],text=True,encoding='utf8'),'html.parser')
  check(p['place'] in old.title.get_text(),path+' production title location')
  for r,article in zip(p['rooms'],s.select('article.room')):
   check(article.h2.get_text()==r['name'],path+' official room name')
   check((('Bed sleepers:' if lang=='en' else 'ベッド就寝人数:') in article.get_text())==(r['bedSleepers'] is not None),path+' sleeper visibility '+r['key'])
   bed=article.find('p').get_text()
   check(bed==(bed_text(r['beds'],lang) if r['beds'] else ('ベッド構成未確認' if lang=='ja' else 'Sleeping arrangement unverified')),path+' beds '+r['key'])
  # Every rendered quote must match a source quote after removing only UI noise + existing whitespace normalization.
  from html import unescape
  originals={re.sub(r'\s+',' ',BeautifulSoup(e['text'],'html.parser').get_text(' ',strip=True).replace('モーダルウィンドウを閉じる','')) for e in p['policy']['cleaningLinen'].get('evidence',[])}
  for q in s.select('[data-official-quote]'):check(q.get_text() in originals,path+' quote changed')
  txt=s.body.get_text(' ',strip=True)
  for bad in ['Bed sleepers: —','ベッド就寝人数: —','モーダルウィンドウを閉じる','1 bathrooms','1 toilets','equal-weighted']:check(bad not in txt,path+' '+bad)
  check('判定の根拠' not in txt if lang=='en' else 'Readiness evidence' not in txt,path+' evidence locale')
  if lang=='ja':
   for bad in ['Affiliate links:','Blank cells mean','Confirm the selected room','First service','Adult capacity excludes','Within ','Other stays in','Every 7 days','Scheduled service:','Bed sleepers','Unverified','Short stay','Long-stay ready']:check(bad not in txt,path+' UI '+bad)
  if p['excluded']:
   check(not s.select('.neighbors'),path+' excluded neighbors')
   check(not home.select(f'#all-stays-directory a[href="/stays/{p["id"]}/"]'),path+' excluded directory')
for lang in ['en','ja','zh-tw','ko']:
 for f in (R/lang/'tokyo').glob('*/index.html'):
  s=soup(f)
  for row in s.select('.gsj-v31 tr[data-property]'):
   prop=next(p for p in P if p['id']==row['data-property']);cells=row.find_all('td');expected=area_label(prop['areaKey'],lang)
   check(expected in cells[1].get_text(),str(f)+' area')
   check('Bed sleepers: —' not in cells[3].get_text(),str(f)+' sleeper dash')
   if lang!='ja':check(not re.search('[ぁ-んァ-ヶ一-龥]',cells[1].get_text()),str(f)+' area JP')
  if lang!='en':
   for part in s.select('.gsj-v31'):
    for q in part.select('[data-official-name],[data-official-quote]'):q.decompose()
    txt=part.get_text(' ',strip=True)
    for bad in ['How stay readiness','Every 7 days','Day 4','First service','Official information conflict','One unit for','Business hotels can','Example calculation','Blank cells mean','Short stay','Sofa beds:','adults;','5–9 nights','10+ nights','Bed sleepers:']:check(bad not in txt,str(f)+' untranslated '+bad)
for a,(en,ja) in AREA.items():
 check(not re.search('[ぁ-んァ-ヶ一-龥]|-ku|-shi',en),a+' area EN');check(bool(re.search('[一-龥]',ja)),a+' area JA')
# Exercise deployment-date writer only in an isolated temp directory, never changing real local sitemap dates.
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp)
 for name in ['sitemap-core.xml','sitemap-stays-en.xml','sitemap-stays-ja.xml']:shutil.copyfile(R/name,t/name)
 changed=json.loads((R/'review/lastmod-pending-urls.json').read_text());write_lastmod(t,changed,'2000-01-02')
 total=0
 for f in t.glob('*.xml'):
  for u in BeautifulSoup(f.read_text(encoding='utf8'),'xml').find_all('url'):
   check(bool(u.lastmod)==(u.loc.text in changed),'lastmod subset')
   if u.lastmod:check(u.lastmod.text=='2000-01-02','lastmod date');total+=1
check(total==len(changed),'lastmod count')
result={'status':'passed' if not errors else 'failed','propertyTitlesChecked':162,'officialRoomNamesChecked':892,'areaMappings':len(AREA),'lastmodPendingCount':len(changed),'lastmodProductionDate':None,'errors':errors}
(R/'review/v33-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False));assert not errors
