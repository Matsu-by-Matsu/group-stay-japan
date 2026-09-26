"""Pure evidence-based room model. No network, no mutation of Phase 1 sources."""
import json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def truth(v):return 'yes' if v is True else 'no' if v is False else 'unknown'
def area_key(address):
 s=unicodedata.normalize('NFKC',address or '')
 city=next((c for c in ['Tokyo','Kyoto','Osaka','Chitose'] if c.lower() in s.lower()),None)
 ward=re.search(r'([A-Za-z]+-ku)\b',s)
 if city and ward:return city+' / '+ward[1].lower()
 if city:return city
 # Preserve exact official administrative labels; no invented proximity.
 jp=re.sub(r'〒?\d{3}-?\d{4}\s*','',s)
 jp=re.sub(r'^(?:東京都|京都府|大阪府|北海道|.{2,3}県)','',jp)
 m=re.match(r'(.+?市)(.+?区)?',jp)
 if m:return m[1]+(' / '+m[2] if m[2] else '')
 m=re.match(r'(.+?区)',jp)
 if m:return 'Tokyo / '+{'墨田区':'sumida-ku','荒川区':'arakawa-ku','台東区':'taito-ku','中央区':'chuo-ku'}.get(m[1],m[1])
 return 'unclassified'
def evaluate(conditions,cfg,max_nights=None):
 out=[];level=1
 for rule in cfg['levels']:
  states=[conditions.get(k,'unknown') for k in rule['requires']]
  if rule['level']==4 and max_nights is not None and max_nights<cfg['extendedStayNights']:states.append('no')
  state='not_supported' if 'no' in states else 'unverified' if 'unknown' in states else 'supported'
  out.append({'level':rule['level'],'state':state,'conditions':{k:conditions.get(k,'unknown') for k in rule['requires']}})
  if state=='supported':level=rule['level']
 return level,out

def build():
 cfg=load('config/stay-rules.json');src=load('data/room-types-source.json')['properties'];inv={p['id']:p for p in load('data/inventory-source.json')['properties']};pol={p['id']:p['fields'] for p in load('data/long-stay-source.json')['properties']};out=[]
 identities={x['id']:x for x in load('data/official-identities.json')}
 for p in src:
  old=dict(inv[p['id']]);identity=identities[p['id']];addresses=identity['officialAddressEvidence'];address=addresses[-1] if p['id'].startswith('minn-') else addresses[0] if addresses else old['address'];address=re.sub(r'^Address | View Map.*| TEL.*| 電話番号.*| この施設に関する質問.*','',address);old['address']=address;policy=pol[p['id']];rooms=[]
  clean=policy['cleaningLinen']['status']=='official_statement_found' or p['id'] in cfg['cleaningConflictAllowed']
  for i,r in enumerate(p['roomTypes']):
   f=r['fields'];val=lambda k:f[k]['value'];kitchen=None
   if r.get('kitchenPresent',{}).get('value') in [True,False]:kitchen=r['kitchenPresent']['value']
   if re.search(r'\bkitchen\b',str(r.get('kitchenDescription',{}).get('value') or ''),re.I):kitchen=True
   if val('hob') is not None:kitchen=True
   if 'キッチン' in r.get('rawRoomEvidence',''):kitchen=True
   w=val('washingMachine');washer=True if w=='in_room' or isinstance(w,str) and re.search(r'washing machine',w,re.I) else False if w in ['shared','no_in_room','no_in_room_washer_dryer'] else None
   # A disabled combined washer-dryer does not prove absence of a standalone washer.
   conditions={'washer':truth(washer),'kitchen':truth(kitchen),'cleaning':'yes' if clean else 'unknown','extended':'unknown'}
   # Extended eligibility requires an explicit typed verified condition; prose is never guessed.
   limits=policy.get('stayLimits',{}).get('value') or {};plan=policy.get('longStayPlan',{})
   if isinstance(limits,dict) and isinstance(limits.get('allowedNights'),int) and limits['allowedNights']>=cfg['extendedStayNights']:conditions['extended']='yes'
   if plan.get('status')=='official_statement_found' and plan.get('value') is True:conditions['extended']='yes'
   maximum=limits.get('maxNights') if isinstance(limits,dict) else None
   level,levels=evaluate(conditions,cfg,maximum)
   bundle=bool(r.get('unitConfiguration'));cap=val('capacity');area=val('areaM2');beds=r.get('bedComponents',{}).get('value',[])
   rooms.append({'key':str(i),'name':r['name']['value'],'capacity':cap,'capacityBasis':r.get('capacityBasis','official room capacity; child rules not separately confirmed'),'childAllowance':r.get('childAllowance',{}).get('value'),'area':area,'areaText':f['areaM2'].get('evidence'),'areaPerPerson':round(area/cap,2) if area and cap and not bundle else None,'beds':val('beds'),'bedSleepers':sum(b['count'] for b in beds if re.fullmatch(r'single beds?',b['officialType'],re.I)) if beds and all(re.fullmatch(r'single beds?|sofa beds?|futons?',b['officialType'],re.I) for b in beds) else None,'sofaBeds':sum(b['count'] for b in beds if re.search(r'sofa|ソファ',b['officialType'],re.I)) if beds else None,'futons':sum(b['count'] for b in beds if re.search(r'futon|布団',b['officialType'],re.I)) if beds else None,'bedComponents':beds,'bedrooms':val('bedrooms'),'bathrooms':val('bathrooms'),'toilets':val('toilets'),'washer':washer,'washerText':w,'dryer':val('dryer'),'kitchen':kitchen,'hob':val('hob'),'hobBurners':val('hobBurners'),'microwave':val('microwave'),'refrigerator':val('refrigerator'),'cookware':val('cookware'),'tableware':val('tableware'),'level':level,'levels':levels,'conditions':conditions,'bundle':bundle,'bundleNote':r.get('comparisonCaution'),'source':p['source'],'checked':p['retrievedAt'][:10]})
  out.append({'id':p['id'],'name':p['name'],'brand':old['operator'],'place':old['place'],'address':old['address'],'areaKey':area_key(old['address']),'source':p['source'],'checked':p['retrievedAt'][:10],'partner':old.get('partner') or old['source'],'photos':old['photos'],'excluded':p['id'] in cfg['excludedProperties'],'beforeMax':old.get('max'),'max':max((r['capacity'] for r in rooms if r['capacity'] is not None),default=old.get('max')),'rooms':rooms,'policy':policy})
 return out,cfg
if __name__=='__main__':
 out,cfg=build();(ROOT/'data/room-model.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('Model:',len(out),'properties,',sum(len(p['rooms']) for p in out),'room cards')
