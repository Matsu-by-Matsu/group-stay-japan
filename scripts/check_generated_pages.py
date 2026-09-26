from pathlib import Path
import json,subprocess,hashlib
from bs4 import BeautifulSoup
R=Path.cwd();errors=[];paths=[]
for f in list((R/'stays').glob('*/index.html'))+list((R/'ja/stays').glob('*/index.html')):
 s=BeautifulSoup(f.read_text(encoding='utf8'),'html.parser');expected='https://groupstayjapan.synthx.jp/'+f.parent.relative_to(R).as_posix()+'/'
 if s.find('link',rel='canonical')['href']!=expected:errors.append(str(f)+' canonical')
 if len(s.select('link[hreflang]'))!=3:errors.append(str(f)+' hreflang')
 for ld in s.select('script[type="application/ld+json"],script[type="application/json"]'):json.loads(ld.string or ld.text)
 if not s.h1:errors.append(str(f)+' h1')
 paths.append(f.relative_to(R).as_posix())
assert len(paths)==162;assert not errors,errors
old_redirect=subprocess.check_output(['git','show','HEAD:assets/legacy-property-redirect.js']);assert old_redirect.replace(b'\r\n',b'\n')==(R/'assets/legacy-property-redirect.js').read_bytes().replace(b'\r\n',b'\n')
model=json.loads((R/'data/room-model.json').read_text(encoding='utf8'))
for p in model:
 if p['excluded']:
  for u in paths:
   if p['id'] in u:assert ('公式サイトで掲載を確認できません（2026年9月25日時点）' if u.startswith('ja/') else 'could not be confirmed on the official website as of September 25, 2026') in (R/u).read_text(encoding='utf8')
for n in [4,6,8]:
 s=BeautifulSoup((R/f'en/tokyo/hotels-for-{n}-guests/index.html').read_text(encoding='utf8'),'html.parser')
 for row in s.select('tr[data-property]'):assert not next(p for p in model if p['id']==row['data-property'])['excluded']
(R/'review/page-validation.json').write_text(json.dumps({'properties':162,'canonicalHreflangJson':'passed','legacyRedirectUnchangedIgnoringLineEndings':True,'excludedNoticeAndTables':'passed','errors':errors},indent=2),encoding='utf8');print('PASS: 162 canonical/hreflang/JSON pages, excluded notices and comparisons, legacy redirect unchanged (line endings normalized).')
