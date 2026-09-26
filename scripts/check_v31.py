import sys,json,random,subprocess
from pathlib import Path
from bs4 import BeautifulSoup
R=Path.cwd();sys.path.insert(0,str(R/'scripts'));from room_model import build,evaluate
p,c=build();assert len(p)==81
for id,n in {'mimaru-shijo-west':6,'fav-ise':4,'fav-lux-nagasaki':8,'fav-lux-kagoshimatenmonkan':6}.items():assert next(x for x in p if x['id']==id)['max']==n
assert evaluate({'washer':'yes','kitchen':'yes','cleaning':'yes','extended':'unknown'},c)[0]==3
assert evaluate({'washer':'unknown','kitchen':'yes','cleaning':'yes','extended':'yes'},c)[0]==1
assert evaluate({'washer':'yes','kitchen':'yes','cleaning':'yes','extended':'yes'},c,max_nights=19)[0]==3
assert evaluate({'washer':'yes','kitchen':'yes','cleaning':'yes','extended':'yes'},c,max_nights=20)[0]==4
old=[x.text for x in BeautifulSoup((R/'review/urls-before.xml').read_text(encoding='utf8'),'xml').find_all('loc')];new=[]
for fn in ['sitemap-core.xml','sitemap-stays-en.xml','sitemap-stays-ja.xml']:new.extend(x.text for x in BeautifulSoup((R/fn).read_text(encoding='utf8'),'xml').find_all('loc'))
assert len(new)==len(set(new))==181 and set(old)==set(new)
for u in old:
 f=R/u.removeprefix('https://groupstayjapan.synthx.jp/');f=f/'index.html' if u.endswith('/') else f;assert f.is_file(),u
assert 'noindex' not in (R/'_SYSTEM/property.html').read_text(encoding='utf8').lower()
for n in [4,6,8]:assert BeautifulSoup((R/f'en/tokyo/hotels-for-{n}-guests/index.html').read_text(encoding='utf8'),'html.parser').select('tr[data-stay-level]')
for f in (R/'ja/tokyo').glob('*/index.html'):
 before=BeautifulSoup(subprocess.check_output(['git','show','HEAD:'+f.relative_to(R).as_posix()],text=True,encoding='utf8'),'html.parser');after=BeautifulSoup(f.read_text(encoding='utf8'),'html.parser');assert before.title.text==after.title.text and before.h1.text==after.h1.text
rng=random.Random(20260925);pairs=[rng.sample([x['id'] for x in p],2) for _ in range(10)]
def shingles(s):
 b=BeautifulSoup(s,'html.parser');[x.decompose() for x in b(['script','style'])];w=(b.body or b).get_text(' ',strip=True).split();return {tuple(w[i:i+6]) for i in range(len(w)-5)}
def jac(a,b):return len(a&b)/len(a|b) if a|b else 0
scores=[]
for a,b in pairs:
 getold=lambda id:subprocess.check_output(['git','show',f'HEAD:stays/{id}/index.html'],text=True,encoding='utf8');getnew=lambda id:(R/f'stays/{id}/index.html').read_text(encoding='utf8')
 scores.append({'a':a,'b':b,'before':jac(shingles(getold(a)),shingles(getold(b))),'after':jac(shingles(getnew(a)),shingles(getnew(b)))})
result={'tests':'passed','urlCount':181,'addedPageUrls':sorted(set(new)-set(old)),'removedPageUrls':sorted(set(old)-set(new)),'similaritySeed':20260925,'pairs':scores,'meanBefore':sum(x['before'] for x in scores)/10,'meanAfter':sum(x['after'] for x in scores)/10}
(R/'review/local-validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='pairs'}))
