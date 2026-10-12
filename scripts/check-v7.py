"""Read-only v7 acceptance checks. Private reports stay outside the repository."""
import json,re,zipfile,subprocess,importlib.util,sys
sys.dont_write_bytecode=True
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup,Comment,Doctype
R=Path(__file__).resolve().parents[1];O=R.parent/'gsj-v7-20261012'
spec=importlib.util.spec_from_file_location('v7',R/'scripts/apply-v7.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
def parse(b):return BeautifulSoup(b,'html.parser')
with zipfile.ZipFile(O/'baseline.zip') as z:old={p:z.read(p) for p in z.namelist()}
checks={};failures=[];residual=[];names=set();parsed={}
for p in old:
 if p.endswith('.html'):
  s=parse((R/p).read_bytes());parsed[p]=s
  if '/stays/' in '/'+p:names.update(x.get_text(strip=True) for x in s.select('h1,[data-official-name],#room-type option'))
def ck(k,test,detail=None):
 checks[k]=bool(test)
 if not test:failures.append({'check':k,'detail':detail})
for p in ['_SYSTEM/about.html','_SYSTEM/partners.html']:
 hs={a['href'] for a in parsed[p].select('a[href]')};ck(p+' links',{'/'}|{u for l in v.LANGS for u in v.lists(l)}<=hs)
links=json.loads((O/'tokyo-links.json').read_text(encoding='utf8'))
for p,s in parsed.items():
 b=parse(old[p]);isprop='/stays/' in '/'+p;islist='/tokyo/' in '/'+p
 ck(p+' doctype',str(s).lower().startswith('<!doctype html>'))
 ck(p+' booking links',[(a.get('href'),a.get('rel'),a.get('target')) for a in s.select('a[href]') if 'trip.com' in a['href']]==[(a.get('href'),a.get('rel'),a.get('target')) for a in b.select('a[href]') if 'trip.com' in a['href']])
 if p!='index.html':
  ck(p+' title+h1',s.title.get_text()==b.title.get_text() and s.h1.get_text()==b.h1.get_text())
  ck(p+' scripts',[(x.get('src'),x.get_text()) for x in s.select('script') if x.get('type')!='application/ld+json']==[(x.get('src'),x.get_text()) for x in b.select('script') if x.get('type')!='application/ld+json'])
 if isprop or islist:
  ck(p+' breadcrumb',bool(s.select_one('.gsj-v7-breadcrumb a[href="/"]')) and any('BreadcrumbList' in x.get_text() for x in s.select('script[type="application/ld+json"]')))
  ck(p+' canonical',s.select_one('link[rel=canonical]')['href']==b.select_one('link[rel=canonical]')['href'])
 if isprop:
  l='en' if p.startswith('stays/') else p.split('/')[0];slug=p.split('/')[-2]
  actual={x['hreflang']:x['href'] for x in s.select('link[hreflang]')};expected={c:v.BASE+v.route(ll,slug) for ll,c in [('en','en'),('ja','ja'),('zh-tw','zh-Hant'),('ko','ko'),('en','x-default')]};ck(p+' hreflang',actual==expected)
  u=v.route(l,slug)
  if u in links:
   actual=[a['href'] for a in s.select('.gsj-v7-compare a')];ck(p+' matching lists',actual==links[u] and all(slug in parsed[v.file(x)].get_text() or any(slug in a.get('href','') for a in parsed[v.file(x)].select('a')) for x in actual))
  if l in ['en','ja']:ck(p+' room contents',[str(x) for x in s.select('article.room')]==[str(x) for x in b.select('article.room')])
  if l in ['zh-tw','ko']:
   ck(p+' robots',s.select_one('meta[name=robots]')['content']=='index,follow')
   for n in s.body.find_all(string=True):
    if isinstance(n,(Comment,Doctype)) or any(a.name in ['script','style'] or a.has_attr('data-official-name') or a.has_attr('data-official-quote') for a in n.parents):continue
    t=str(n).strip()
    for name in sorted(names,key=len,reverse=True):t=t.replace(name,'')
    t=re.sub(r'GROUP STAY JAPAN|Trip\.com|English|MIMARU|GRAND BASE|FAV LUX|Minn|MINN|fav|m²|m2','',t)
    if re.search(r'[A-Za-z]',t):residual.append({'file':p,'text':str(n).strip(),'remaining':t})
 if islist:
  ck(p+' old source text',not any(w in s.get_text() for w in ['Official source ·','公式出典 ·','官方來源 ·','공식 출처 ·']))
  def external(x):return Counter(a['href'] for a in x.select('table a[href]') if a['href'].startswith('http'))
  ck(p+' source link count',external(s)==external(b))
  def prop_links(x):return Counter(a['href'] for a in x.select('a[href]') if '/stays/' in a['href'])
  ck(p+' property links',prop_links(s)==prop_links(b))
counts=json.loads((O/'card-counts.json').read_text(encoding='utf8'));ck('9 card aggregate checks',len(counts)==9 and all(x['pass'] for x in counts),counts)
s=parsed['index.html'];text=(R/'index.html').read_text(encoding='utf8');ck('home h1',s.h1.get_text()=='Apartment hotels for groups and longer stays in Japan');ck('home16',all(s.select_one('a[href="'+u+'"]') for l in v.LANGS for u in v.lists(l)));ck('home Japanese directory links',len([a for a in s.select('a') if a.get_text()=='日本語'])==0);ck('home template',not any(w in ''.join(x.get_text() for x in s.select('script')) for w in ['card-match','availability-note']))
import xml.etree.ElementTree as E
ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
for l in ['zh-tw','ko']:
 root=E.fromstring((R/('sitemap-stays-'+l+'.xml')).read_bytes());ck(l+' sitemap',len(root)==81 and all(x.find(ns+'lastmod').text=='2026-10-12' for x in root));ck(l+' sitemapindex','sitemap-stays-'+l+'.xml' in (R/'sitemap.xml').read_text())
# Verify lastmod updates only the authorized set; preserve all other sitemap values.
for name in ['sitemap-core.xml','sitemap-stays-en.xml','sitemap-stays-ja.xml']:
 before=E.fromstring(old[name]);after=E.fromstring((R/name).read_bytes())
 def entries(root):return {x.find(ns+'loc').text:(x.find(ns+'lastmod').text if x.find(ns+'lastmod') is not None else None) for x in root}
 bm,am=entries(before),entries(after);ck(name+' URL set',bm.keys()==am.keys())
 authorized={v.BASE+'/'}|{v.BASE+u for ll in v.LANGS for u in v.lists(ll)}|{v.BASE+'/_SYSTEM/'+x+'.html' for x in ['partners','about']}|{v.BASE+u for u in links if u.startswith('/stays/') or u.startswith('/ja/stays/')}
 ck(name+' lastmod',all(value==('2026-10-12' if u in authorized else bm[u]) for u,value in am.items()))
inline=0
for x in parsed['index.html'].select('script:not([src])'):
 if x.get('type') in ['application/ld+json','application/json']:continue
 r=subprocess.run(['node','--check'],input=x.get_text(),text=True,encoding='utf-8',capture_output=True);ck('home JS syntax '+str(inline),r.returncode==0,r.stderr);inline+=1
status=subprocess.check_output(['git','status','--short'],cwd=R).decode();allowed=set(old)|{'sitemap-stays-zh-tw.xml','sitemap-stays-ko.xml','scripts/apply-v7.py','scripts/check-v7.py'};changed=[line[3:].strip('"') for line in status.splitlines()];ck('scope',set(changed)<=allowed,sorted(set(changed)-allowed))
ck('E1 English residual',not residual,{'count':len(residual)})
(O/'english-residuals.json').write_text(json.dumps(residual,ensure_ascii=False,indent=2),encoding='utf8');(O/'validation.json').write_text(json.dumps({'checks':checks,'failures':failures},ensure_ascii=False,indent=2),encoding='utf8');(O/'git-status.txt').write_text(status,encoding='utf8')
md='# v7改訂版2 ローカル検証報告\n\ncommit・pushは未実施。\n\n'+f'チェック: {sum(checks.values())}/{len(checks)} 合格。英語残存: {len(residual)} 箇所。\n\n## 不合格\n'+json.dumps(failures,ensure_ascii=False,indent=2)+'\n\n## カード集計\n'+json.dumps(counts,ensure_ascii=False,indent=2)+'\n\n## 添付\n- tokyo-links.json: 東京104ページからの一覧リンク\n- area-translations.json: 地名対照表\n- english-residuals.json: 許可リスト以外の英字残存\n- git-status.txt: 変更ファイル一覧\n- baseline.zip: 変更前の全対象ファイル\n'
(O/'V7-REPORT.md').write_text(md,encoding='utf8');print(json.dumps({'passed':sum(checks.values()),'total':len(checks),'failures':failures,'residualUnique':sorted(set(r['remaining'] for r in residual))},ensure_ascii=False))