"""Add supplied bed-sleeper facts to current HTML, without rebuilding pages.
Run: python scripts/add-bed-sleepers.py --date YYYY-MM-DD
Counts come exclusively from config/bed-sleepers.json. No inference of bedding.
"""
import argparse, json, re
from collections import Counter, defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
LANGS=['en','ja','zh-tw','ko']
ROOM_LABELS=[['Real beds for all {cap} guests', '定員{cap}人全員がベッドで寝られます', '{cap}位住客全都有床可睡', '정원 {cap}명 모두 침대에서 잘 수 있습니다'], ['Real beds for {b} of {cap} guests · {r} on sofa beds, day beds or futons', 'ベッドで寝られるのは{cap}人中{b}人。残り{r}人はソファベッド・デイベッド・布団です', '{cap}位中有{b}位有床可睡，其餘{r}位睡沙發床、坐臥兩用床或日式床墊', '{cap}명 중 {b}명이 침대에서 잘 수 있습니다. 나머지 {r}명은 소파베드·데이베드·요이불입니다'], ['Real beds for {b} of {cap} guests · {o} on sofa beds, day beds or futons · check the official site for how {cap} guests sleep', 'ベッドで寝られるのは{cap}人中{b}人、ソファベッド・デイベッド・布団で{o}人。{cap}人で泊まるときの寝方は公式サイトで確認してください', '{cap}位中有{b}位有床可睡，{o}位睡沙發床、坐臥兩用床或日式床墊。{cap}人入住時的睡法請至官方網站確認', '{cap}명 중 {b}명은 침대, {o}명은 소파베드·데이베드·요이불입니다. {cap}명이 묵을 때의 잠자리는 공식 사이트에서 확인하세요'], ['Real beds for {b} of {cap} guests · check the official site for how {cap} guests sleep', 'ベッドで寝られるのは{cap}人中{b}人。{cap}人で泊まるときの寝方は公式サイトで確認してください', '{cap}位中有{b}位有床可睡。{cap}人入住時的睡法請至官方網站確認', '{cap}명 중 {b}명이 침대에서 잘 수 있습니다. {cap}명이 묵을 때의 잠자리는 공식 사이트에서 확인하세요'], ['Check the official site for the bed breakdown', '寝具の内訳は公式サイトで確認してください', '床型明細請至官方網站確認', '침대 구성은 공식 사이트에서 확인하세요']]
CARD_LABELS=[['{N}人全員がベッドで寝られる客室：{k}室', '{N}人全都有床可睡的房型：{k}種', '{N}명 모두 침대에서 잘 수 있는 객실: {k}개'], ['{N}人全員がベッドで寝られる客室はありません', '沒有可讓{N}人全都睡床的房型', '{N}명 모두 침대에서 잘 수 있는 객실은 없습니다'], ['{N}人全員がベッドで寝られるかは、公式サイトで寝具を確認してください', '{N}人是否全都有床可睡，請至官方網站確認床型', '{N}명 모두 침대에서 잘 수 있는지는 공식 사이트에서 침대 구성을 확인하세요'], ['1室で{N}人が泊まれる客室はありません。掲載上の最大定員は、複数の客室をまとめた貸切の人数です', '沒有可供{N}人同住一間的房型。刊載的最多入住人數為多間客房合併包租的人數', '{N}명이 한 객실에 묵을 수 있는 객실은 없습니다. 표시된 최대 정원은 여러 객실을 묶은 전체 대여 기준입니다']]
NOTES=['How we count: single, semi-double and loft beds = 1 person; double, queen and king beds = 2; each bunk bed = 2. Sofa beds, day beds and futons are counted separately. Bed details from the official sites (checked 2026-09-25).', '数え方：シングル・セミダブル・ロフトベッドは1人、ダブル・クイーン・キングは2人、二段ベッドは1台2人。ソファベッド・デイベッド・布団は別に数えています。寝具は公式サイトの記載（2026/9/25確認）。', '計算方式：單人床、小雙人床、閣樓床各算1人；雙人床、加大雙人床、特大雙人床各算2人；上下舖每組算2人。沙發床、坐臥兩用床、日式床墊另計。床型依官方網站（2026/9/25確認）。', '계산 방법: 싱글·세미더블·로프트 침대는 1명, 더블·퀸·킹 침대는 2명, 2층 침대는 1대에 2명. 소파베드·데이베드·요이불은 따로 셉니다. 침대 구성은 공식 사이트 기준(2026/9/25 확인).']

def read(path):
    return path.read_bytes().decode('utf-8')

def state(room):
    if room['status']=='ambiguous': return 'check'
    b,o,cap=room['bedSleepers'],room['otherSleepers'],room['capacity']
    return 'all' if b>=cap else 'partial' if b+o>=cap else 'gap'

def cleanup(s):
    for badge in s.select('.gsj-beds-badge'):
        prev=badge.previous_sibling
        if getattr(prev,'name',None)=='br': prev.decompose()
    for el in s.select('.gsj-beds,.gsj-beds-summary,.gsj-beds-note,.gsj-beds-badge,.gsj-beds-card,.gsj-beds-filters'):
        el.decompose()
    for el in s.select('[data-all-beds]'): del el['data-all-beds']
    for el in s.select('link[href*="/assets/gsj-beds.css"],script[src*="/assets/gsj-beds.js"]'): el.decompose()

def serialize(s,original):
    # html.parser inserts one doctype newline on nine legacy guide pages.
    prefix=re.match(r'<!DOCTYPE html>(\s*)',original).group(1)
    return re.sub(r'\A<!DOCTYPE html>\s*',lambda m:'<!DOCTYPE html>'+prefix,str(s),count=1)

def tag(s,name,cls,text=None,**attrs):
    el=s.new_tag(name,attrs={'class':cls,**attrs})
    if text is not None: el.string=text
    return el

def summaries(lang,m,n,a,N=None):
    i=LANGS.index(lang)
    if N is None:
        text=[f'Everyone gets a real bed at full capacity in {n} of {m} room types',f'定員いっぱいでも全員がベッドで寝られる客室：{m}室中{n}室',f'滿房時全員都有床可睡的房型：{m}種中{n}種',f'정원이 다 차도 모두 침대에서 잘 수 있는 객실: {m}개 중 {n}개'][i]
        if a: text+=[f' · {a} need checking on the official site',f'（{a}室は公式サイトで確認が必要）',f'（{a}種需至官方網站確認）',f' ({a}개는 공식 사이트에서 확인 필요)'][i]
    else:
        text=[f'{n} of {m} room types here give all {N} guests a real bed.',f'この一覧の{m}室のうち、{N}人全員がベッドで寝られるのは{n}室です。',f'此清單{m}種房型中，{N}人全都有床可睡的有{n}種。',f'이 목록의 {m}개 객실 중 {N}명 모두 침대에서 잘 수 있는 객실은 {n}개입니다.'][i]
        if a: text+=[f' {a} need checking on the official site.',f'{a}室は公式サイトで確認が必要です。',f'{a}種需至官方網站確認。',f' {a}개는 공식 사이트에서 확인이 필요합니다.'][i]
    return text

def add_summary(s,anchor,lang,m,n,a,N=None):
    summary=tag(s,'p','gsj-beds-summary',summaries(lang,m,n,a,N))
    anchor.insert_after(summary)
    summary.insert_after(tag(s,'p','gsj-beds-note',NOTES[LANGS.index(lang)]))

def assets(s,english_list=False):
    s.head.append(s.new_tag('link',rel='stylesheet',href='/assets/gsj-beds.css?v=20261003'))
    if english_list:
        anchor=s.find('script',src=re.compile(r'/assets/gsj-readiness\.js'))
        assert anchor is not None
        anchor.insert_after(s.new_tag('script',src='/assets/gsj-beds.js?v=20261003',defer=True))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--date',default=datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d'))
    day=parser.parse_args().date;datetime.strptime(day,'%Y-%m-%d')
    data=json.loads(read(ROOT/'config/bed-sleepers.json'))['properties']
    excluded=set(json.loads(read(ROOT/'config/stay-rules.json'))['excludedProperties'])
    pending={}; stats={}; cohorts={}; changed_urls=set()
    def load(path):
        original=read(ROOT/path);s=BeautifulSoup(original,'html.parser');cleanup(s)
        return original,s
    def save(path,s,original,guide=False):
        assets(s,guide);output=serialize(s,original)
        if guide or '/tokyo/' in path:
            output,count=re.subn(r'("dateModified"\s*:\s*")[^"]+("|$)',lambda m:m[1]+day+m[2],output)
            assert count==1,(path,'dateModified',count)
        # Removal must recover existing content exactly, apart from permitted dateModified.
        old=BeautifulSoup(original,'html.parser');cleanup(old)
        cleaned=BeautifulSoup(output,'html.parser');cleanup(cleaned)
        norm=lambda t:re.sub(r'("dateModified"\s*:\s*")[^"]+"',r'\1DATE"',t) if '/tokyo/' in path else t
        assert norm(serialize(cleaned,original))==norm(serialize(old,original)),path
        pending[path]=output
        changed_urls.add('https://groupstayjapan.synthx.jp/'+path.removesuffix('index.html'))
    for lang in LANGS:
        counts=Counter()
        for slug,rooms in data.items():
            if slug in excluded: continue
            path=('' if lang=='en' else lang+'/')+f'stays/{slug}/index.html'
            original,s=load(path);articles=s.select('article.room')
            assert [a['id'] for a in articles]==[r['id'] for r in rooms],path
            for article,room in zip(articles,rooms):
                status=state(room);counts[status]+=1
                idx={'all':0,'partial':1,'check':4}.get(status,2 if room.get('otherSleepers',0)>=1 else 3)
                values={'cap':room['capacity'],'b':room.get('bedSleepers'),'o':room.get('otherSleepers'),'r':room['capacity']-room.get('bedSleepers',0)}
                text=ROOM_LABELS[idx][LANGS.index(lang)].format(**values)
                if lang=='en' and status=='all' and room['capacity']==2:text='Real beds for both guests'
                metrics=article.select('div.metrics');assert len(metrics)==1
                metrics[0].insert_after(tag(s,'p','gsj-beds gsj-beds-'+status,text))
            add_summary(s,s.select_one('p.gsj-readiness-summary'),lang,len(rooms),sum(state(r)=='all' for r in rooms),sum(state(r)=='check' for r in rooms))
            save(path,s,original)
        stats[lang]=dict(counts)
    for N in [4,6,8]:
        path=f'en/tokyo/hotels-for-{N}-guests/index.html';original,s=load(path)
        groups=defaultdict(list);counts=Counter();rows=s.select('.gsj-readiness-table tr[data-property]')
        for row in rows:
            slug=row['data-property'];assert slug not in excluded
            key='room-'+parse_qs(urlsplit(row.find_all('td')[0].a['href']).query)['room'][0]
            room=next(r for r in data[slug] if r['id']==key);groups[slug].append(room)
            val='check' if room['status']=='ambiguous' else '1' if room['bedSleepers']>=N else '0'
            row['data-all-beds']=val;counts[val]+=1
            label='Check beds on the official site' if val=='check' else f'All {N} in real beds' if val=='1' else f'Real beds for {room["bedSleepers"]} of {N}'
            cell=row.find_all('td')[3];cell.append(s.new_tag('br'));cell.append(tag(s,'span','gsj-beds-badge gsj-beds-badge-'+{'1':'yes','0':'no','check':'check'}[val],label))
        m,n,a=len(rows),counts['1'],counts['check'];cohorts[N]={'m':m,'n':n,'a':a,'cards':{}}
        heading=s.find('h2',string=f'Compare exact rooms for {N} guests');assert heading
        add_summary(s,heading.find_next_sibling('p'),'en',m,n,a,N)
        for anchor in s.select('.gsj-readiness-filters'):
            bar=tag(s,'div','gsj-beds-filters',role='group',**{'aria-label':'Beds'})
            button=s.new_tag('button',type='button',attrs={'data-beds-filter':'','aria-pressed':'false'});button.string=f'Only rooms where all {N} get a real bed';bar.append(button);anchor.insert_after(bar)
        save(path,s,original,True)
        for lang in LANGS[1:]:
            path=f'{lang}/tokyo/{N}-guests/index.html';original,s=load(path);cc=Counter()
            for card in s.select('.grid > article.card'):
                slug=card.select_one('a.photo[data-stay]')['data-stay'];assert slug not in excluded
                rr=groups[slug];k=sum(r['status']=='ok' and r['bedSleepers']>=N for r in rr);aa=sum(r['status']=='ambiguous' for r in rr)
                category=0 if k else 2 if aa else 1
                if not rr:
                    assert slug=='mimaru-ueno-inaricho' and N in [6,8],('Unexpected empty English cohort',path,slug)
                    category=3
                cc[str(category)]+=1
                label=CARD_LABELS[category][LANGS.index(lang)-1].format(N=N,k=k)
                card.select_one('.body > dl').insert_after(tag(s,'p','gsj-beds-card'+(' gsj-beds-card-yes' if k else ''),label))
            head=s.select_one('.grid').find_parent('section',class_='content').select_one('.head > p')
            add_summary(s,head,lang,m,n,a,N);save(path,s,original);cohorts[N]['cards'][lang]=dict(cc)
    for path in ['sitemap-core.xml','sitemap-stays-en.xml','sitemap-stays-ja.xml']:
        original=read(ROOT/path)
        def replace(match):
            block=match[0];url=re.search(r'<loc>(.*?)</loc>',block)[1]
            if url in changed_urls:
                assert '<lastmod>' in block
                return re.sub(r'<lastmod>[^<]+</lastmod>',f'<lastmod>{day}</lastmod>',block)
            return block
        pending[path]=re.sub(r'<url>.*?</url>',replace,original,flags=re.S)
    for path,output in pending.items(): (ROOT/path).write_bytes(output.encode('utf8'))
    print(json.dumps({'date':day,'properties':stats,'lists':cohorts,'html':len(pending)-3,'files':len(pending)},ensure_ascii=True,indent=2))

if __name__=='__main__': main()
