import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const root = path.resolve(import.meta.dirname, '..');
const indexSource = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const catalogSource = fs.readFileSync(path.join(root, '_SYSTEM', 'catalog.js'), 'utf8');
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(catalogSource, sandbox);

const baseMatch = indexSource.match(/const stays=\[([\s\S]*?)\n\s*\];\s*\n\s*stays\.push/);
if (!baseMatch) throw new Error('Could not locate the base stays array in index.html');
const baseStays = vm.runInNewContext(`[${baseMatch[1]}]`);
const allStays = [...baseStays, ...(sandbox.window.GSJ_EXTRA_STAYS || [])];
const stays = allStays
  .filter((stay) => stay.city === 'tokyo' && Number(stay.max) >= 6)
  .sort((a, b) => Number(b.max) - Number(a.max) || a.name.localeCompare(b.name));

if (!stays.length) throw new Error('No Tokyo stays with verified capacity of six or more were found');

const locales = {
  en: {
    code: 'en', dir: 'en/tokyo/hotels-for-6-guests', label: 'English',
    title: 'Hotels in Tokyo for 6 People | GROUP STAY JAPAN',
    description: 'Compare Tokyo hotels and apartment stays for 6 people. See maximum occupancy, room size, kitchens and group-friendly features before checking live availability on Trip.com.',
    eyebrow: 'Tokyo stays for six', h1: 'Hotels in Tokyo for 6 People',
    lead: 'A practical shortlist for families and friends who want to stay together. Every property below has a listed room capacity of at least six guests; the exact room type and live availability must be confirmed on the booking site.',
    count: `${stays.length} group stays to compare`, listTitle: 'Compare stays for your group of six',
    max: 'Maximum listed capacity', size: 'Room size', feature: 'Group features',
    details: 'View room details', note: 'Room capacity varies by room type. Enter your dates on the property page and confirm the final room, price and conditions on Trip.com.',
    guideTitle: 'How to choose a Tokyo stay for six',
    guides: [
      ['Check the sleeping layout', 'A room that accepts six guests may combine regular beds, bunk beds, sofa beds or futons. Confirm who sleeps where before booking.'],
      ['Look beyond capacity', 'For longer stays, a dining table, kitchen, washer and shared living space can matter as much as the number of beds.'],
      ['Confirm one room', 'Availability changes by date and room type. On Trip.com, verify that the selected plan accommodates all six guests in the room arrangement you expect.']
    ],
    faqTitle: 'Frequently asked questions', faqs: [
      ['Can six people stay in one hotel room in Tokyo?', 'Yes. Apartment hotels and selected group-oriented properties offer room types for six or more guests. Capacity depends on the individual room type, not only the hotel.'],
      ['Does GROUP STAY JAPAN show live availability?', 'No. This page organizes verified group-capacity information. Live availability, final prices, taxes and cancellation terms are confirmed on Trip.com.'],
      ['Are all six guests guaranteed regular beds?', 'Not necessarily. Some room types use sofa beds, bunk beds or futons. Check the room and bed description on the booking site before completing the reservation.']
    ],
    back: '← GROUP STAY JAPAN', home: 'Search all group stays', disclaimer: 'Affiliate disclosure: GROUP STAY JAPAN may receive a commission from qualifying bookings at no additional cost to the traveler.'
  },
  ja: {
    code: 'ja', dir: 'ja/tokyo/6-guests', label: '日本語',
    title: '東京で6人が一緒に泊まれるホテル | GROUP STAY JAPAN',
    description: '東京で6人が同じ部屋に泊まれるホテル・アパートメントホテルを比較。最大定員、客室面積、キッチンなどを確認してからTrip.comで空室と最終料金を確認できます。',
    eyebrow: '東京・6人向けの宿', h1: '東京で6人が一緒に泊まれるホテル',
    lead: '家族や友人6人が、できる限り同じ部屋で過ごすための宿を比較できます。以下は最大定員が6名以上と確認できる施設です。実際の客室タイプ、空室、最終料金は予約先でご確認ください。',
    count: `${stays.length}軒のグループ向け施設`, listTitle: '6人旅行に合う宿を比較',
    max: '確認済み最大定員', size: '客室面積', feature: 'グループ向け設備',
    details: '客室情報を見る', note: '定員は客室タイプにより異なります。施設詳細で日付を入力し、Trip.comで最終的な客室・料金・条件をご確認ください。',
    guideTitle: '東京で6人用の宿を選ぶポイント',
    guides: [
      ['寝具構成を確認', '定員6名でも、通常ベッドのほかに二段ベッド、ソファベッド、布団を使用する場合があります。予約前に誰がどこで寝るか確認しましょう。'],
      ['定員以外の快適性を見る', '連泊では、ダイニングテーブル、キッチン、洗濯機、全員で過ごせるリビング空間も重要です。'],
      ['同じ部屋か最終確認', '空室は日付と客室タイプにより変わります。Trip.comで、選択したプランが6名全員を想定した客室構成か確認してください。']
    ],
    faqTitle: 'よくある質問', faqs: [
      ['東京で6人が同じホテル客室に泊まれますか？', 'はい。アパートメントホテルなどには6名以上に対応する客室タイプがあります。定員はホテル単位ではなく客室タイプごとに確認が必要です。'],
      ['GSJでリアルタイムの空室を確認できますか？', '現在はできません。GSJではグループ定員情報を整理し、空室、最終料金、税金、キャンセル条件はTrip.comで確認いただきます。'],
      ['6人全員に通常のベッドがありますか？', '施設・客室によって異なります。ソファベッド、二段ベッド、布団を使用する場合があるため、予約前に寝具説明をご確認ください。']
    ],
    back: '← GROUP STAY JAPAN', home: 'すべてのグループ向け宿を検索', disclaimer: 'アフィリエイトについて：対象予約が成立した場合、旅行者の追加負担なしでGROUP STAY JAPANが紹介報酬を受け取ることがあります。'
  },
  'zh-tw': {
    code: 'zh-Hant', dir: 'zh-tw/tokyo/6-guests', label: '繁體中文',
    title: '東京6人住宿｜可一起入住的飯店 | GROUP STAY JAPAN',
    description: '比較適合6人同行的東京飯店與公寓式飯店。查看最多入住人數、房間大小、廚房與團體設備，再前往Trip.com確認即時空房與最終價格。',
    eyebrow: '東京6人同行住宿', h1: '東京可供6人一起入住的飯店',
    lead: '為希望住在同一空間的家庭與朋友整理實用住宿名單。以下設施已確認至少有最多容納6人的房型；實際房型、即時空房與最終價格請在預訂網站確認。',
    count: `${stays.length}間團體友善住宿`, listTitle: '比較適合6人同行的住宿',
    max: '已確認最多入住人數', size: '客房面積', feature: '團體住宿設備',
    details: '查看客房資訊', note: '入住人數依房型而異。請在設施頁面輸入日期，並於Trip.com確認最終房型、價格與條件。',
    guideTitle: '如何選擇東京6人住宿',
    guides: [
      ['確認床位配置', '可住6人的房型可能搭配一般床、上下舖、沙發床或日式床墊。預訂前請確認每位旅客的睡眠安排。'],
      ['不只看入住人數', '長住時，餐桌、廚房、洗衣機以及全員可共處的客廳空間同樣重要。'],
      ['確認是否同一房間', '空房會依日期與房型改變。請在Trip.com確認所選方案是否能依預期讓6位旅客入住。']
    ],
    faqTitle: '常見問題', faqs: [
      ['6個人可以住在東京同一間飯店客房嗎？', '可以。公寓式飯店及部分團體住宿提供6人以上房型，但必須依個別房型確認，而不是只看飯店名稱。'],
      ['GROUP STAY JAPAN會顯示即時空房嗎？', '目前不會。本頁整理已確認的團體入住人數；即時空房、最終價格、稅費與取消條件請於Trip.com確認。'],
      ['6位旅客都有一般床鋪嗎？', '不一定。部分房型使用沙發床、上下舖或日式床墊，完成預訂前請確認房型與床位說明。']
    ],
    back: '← GROUP STAY JAPAN', home: '搜尋所有團體住宿', disclaimer: '聯盟行銷說明：符合條件的預訂成立時，GROUP STAY JAPAN可能獲得佣金，旅客不需支付額外費用。'
  },
  ko: {
    code: 'ko', dir: 'ko/tokyo/6-guests', label: '한국어',
    title: '도쿄 6인 숙소｜한 객실에서 함께 머무는 호텔 | GROUP STAY JAPAN',
    description: '6명이 함께 머물 수 있는 도쿄 호텔과 아파트먼트 호텔을 비교하세요. 최대 정원, 객실 크기, 주방과 그룹 편의시설을 확인한 뒤 Trip.com에서 실시간 객실과 최종 요금을 확인할 수 있습니다.',
    eyebrow: '도쿄 6인 여행 숙소', h1: '도쿄에서 6명이 함께 머물 수 있는 호텔',
    lead: '가족이나 친구 6명이 가능한 한 같은 공간에서 머물기 위한 숙소를 비교합니다. 아래 시설은 최대 정원 6명 이상의 객실이 확인된 곳이며, 실제 객실 유형과 실시간 객실, 최종 요금은 예약 사이트에서 확인해야 합니다.',
    count: `${stays.length}개의 그룹 숙소`, listTitle: '6인 여행에 맞는 숙소 비교',
    max: '확인된 최대 정원', size: '객실 면적', feature: '그룹 편의시설',
    details: '객실 정보 보기', note: '정원은 객실 유형에 따라 다릅니다. 시설 상세에서 날짜를 입력하고 Trip.com에서 최종 객실, 요금과 조건을 확인하세요.',
    guideTitle: '도쿄 6인 숙소 선택 방법',
    guides: [
      ['침대 구성을 확인하세요', '정원 6명 객실도 일반 침대와 함께 이층 침대, 소파베드 또는 요이불을 사용할 수 있습니다. 예약 전 각자의 취침 위치를 확인하세요.'],
      ['정원 외의 편안함도 보세요', '장기 숙박이라면 식탁, 주방, 세탁기와 모두가 함께 지낼 수 있는 거실 공간도 중요합니다.'],
      ['한 객실인지 최종 확인하세요', '객실은 날짜와 객실 유형에 따라 달라집니다. Trip.com에서 선택한 상품이 예상한 구성으로 6명 전원을 수용하는지 확인하세요.']
    ],
    faqTitle: '자주 묻는 질문', faqs: [
      ['도쿄에서 6명이 한 호텔 객실에 머물 수 있나요?', '네. 아파트먼트 호텔과 일부 그룹 숙소에는 6명 이상 객실이 있습니다. 호텔 전체가 아니라 개별 객실 유형의 정원을 확인해야 합니다.'],
      ['GROUP STAY JAPAN에서 실시간 객실을 확인할 수 있나요?', '현재는 제공하지 않습니다. 이 페이지는 확인된 그룹 정원 정보를 정리하며, 실시간 객실, 최종 요금, 세금과 취소 조건은 Trip.com에서 확인합니다.'],
      ['6명 모두 일반 침대를 이용하나요?', '숙소와 객실에 따라 다릅니다. 소파베드, 이층 침대 또는 요이불을 사용할 수 있으므로 예약 전 침대 설명을 확인하세요.']
    ],
    back: '← GROUP STAY JAPAN', home: '모든 그룹 숙소 검색', disclaimer: '제휴 안내: 조건에 맞는 예약이 완료되면 여행자의 추가 비용 없이 GROUP STAY JAPAN이 수수료를 받을 수 있습니다.'
  }
};

const languageLinks = Object.values(locales).map((locale) => ({ locale, href: `https://groupstayjapan.synthx.jp/${locale.dir}/` }));

const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const imageUrl = (value) => value.startsWith('http') ? value : `https://groupstayjapan.synthx.jp/${value.replace(/^\.\//, '')}`;

function renderPage(locale) {
  const canonical = `https://groupstayjapan.synthx.jp/${locale.dir}/`;
  const cards = stays.map((stay) => `
        <article class="card">
          <a class="photo" href="/\_SYSTEM/property.html?id=${encodeURIComponent(stay.id)}&guests=6&lang=${encodeURIComponent(locale.code === 'zh-Hant' ? 'zh-TW' : locale.code)}">
            <img src="${escapeHtml(imageUrl(stay.img))}" alt="${escapeHtml(stay.name)}" loading="lazy">
            <span>${escapeHtml(stay.operator)} · ${escapeHtml(locale.max)} ${escapeHtml(stay.max)}</span>
          </a>
          <div class="body"><p class="place">${escapeHtml(stay.place)}</p><h2>${escapeHtml(stay.name)}</h2>
            <dl><div><dt>${escapeHtml(locale.max)}</dt><dd>${escapeHtml(stay.max)}</dd></div><div><dt>${escapeHtml(locale.size)}</dt><dd>${escapeHtml(stay.size)}</dd></div><div><dt>${escapeHtml(locale.feature)}</dt><dd>${escapeHtml(stay.feature)}</dd></div></dl>
            <a class="button" href="/\_SYSTEM/property.html?id=${encodeURIComponent(stay.id)}&guests=6&lang=${encodeURIComponent(locale.code === 'zh-Hant' ? 'zh-TW' : locale.code)}">${escapeHtml(locale.details)} →</a>
          </div>
        </article>`).join('');
  const faqsJson = locale.faqs.map(([name, text]) => ({ '@type': 'Question', name, acceptedAnswer: { '@type': 'Answer', text } }));
  const itemList = stays.map((stay, index) => ({ '@type': 'ListItem', position: index + 1, name: stay.name, url: `https://groupstayjapan.synthx.jp/_SYSTEM/property.html?id=${encodeURIComponent(stay.id)}` }));
  return `<!doctype html>
<html lang="${locale.code}"><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-GVQ24M4R7R"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-GVQ24M4R7R');</script>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(locale.title)}</title><meta name="description" content="${escapeHtml(locale.description)}"><link rel="canonical" href="${canonical}">
${languageLinks.map(({ locale: item, href }) => `<link rel="alternate" hreflang="${item.code}" href="${href}">`).join('\n')}<link rel="alternate" hreflang="x-default" href="${languageLinks[0].href}">
<meta property="og:type" content="website"><meta property="og:title" content="${escapeHtml(locale.title)}"><meta property="og:description" content="${escapeHtml(locale.description)}"><meta property="og:url" content="${canonical}"><meta property="og:image" content="${escapeHtml(imageUrl(stays[0].img))}">
<script type="application/ld+json">${JSON.stringify({ '@context': 'https://schema.org', '@graph': [{ '@type': 'CollectionPage', name: locale.h1, description: locale.description, url: canonical, mainEntity: { '@type': 'ItemList', numberOfItems: stays.length, itemListElement: itemList } }, { '@type': 'FAQPage', mainEntity: faqsJson }] })}</script>
<style>:root{--ink:#14231d;--green:#164c39;--lime:#d8f26f;--paper:#f7f6f1;--muted:#64716b;--line:#dfe4df}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,"Noto Sans",sans-serif;line-height:1.65}a{color:inherit;text-decoration:none}.wrap{width:min(1160px,calc(100% - 36px));margin:auto}.header{padding:20px 0;background:#103a2c;color:#fff}.nav{display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{font-weight:900;letter-spacing:.08em}.langs{display:flex;gap:7px;flex-wrap:wrap}.langs a{padding:7px 10px;border:1px solid #ffffff66;border-radius:999px;font-size:12px}.langs a[aria-current]{background:#fff;color:var(--green)}.hero{padding:76px 0 58px;background:linear-gradient(135deg,#123f30,#1c6249);color:#fff}.eyebrow{color:var(--lime);font-size:12px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}.hero h1{max-width:850px;margin:12px 0 20px;font-size:clamp(42px,7vw,76px);line-height:1.02;letter-spacing:-.055em}.lead{max-width:780px;color:#ffffffd9;font-size:17px}.count{display:inline-block;margin-top:20px;padding:8px 13px;border-radius:999px;background:var(--lime);color:var(--green);font-weight:800}.content{padding:68px 0}.section-head{margin-bottom:28px}.section-head h2,.guide h2,.faq h2{margin:0 0 10px;font-size:clamp(28px,4vw,42px);line-height:1.12}.section-head p{max-width:800px;color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}.card{overflow:hidden;background:#fff;border:1px solid var(--line);border-radius:20px;box-shadow:0 8px 30px #1535290d}.photo{height:220px;display:block;position:relative;overflow:hidden;background:#e2e6e3}.photo img{width:100%;height:100%;object-fit:cover}.photo span{position:absolute;left:12px;top:12px;padding:7px 9px;border-radius:999px;background:var(--lime);color:var(--green);font-size:10px;font-weight:800}.body{padding:18px}.place{margin:0;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.1em}.body h2{min-height:52px;margin:5px 0 14px;font-size:19px;line-height:1.35}.body dl{margin:0 0 17px}.body dl div{display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px solid #edf0ed;font-size:11px}.body dt{color:var(--muted)}.body dd{margin:0;text-align:right;font-weight:700}.button{display:block;padding:11px 12px;border-radius:10px;background:var(--green);color:#fff;text-align:center;font-size:12px;font-weight:800}.guide{padding:65px 0;background:#ede9df}.guide-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:25px}.tip{padding:24px;background:#fff;border-radius:17px}.tip b{display:block;margin-bottom:8px}.tip p{margin:0;color:var(--muted);font-size:14px}.faq{padding:68px 0}.faq details{max-width:850px;padding:18px 0;border-bottom:1px solid var(--line)}.faq summary{cursor:pointer;font-weight:800}.faq details p{color:var(--muted)}.footer{padding:38px 0;background:#0d2c21;color:#ffffffb8}.footer-inner{display:flex;justify-content:space-between;gap:25px}.footer a{color:#fff;font-weight:700}.small{font-size:11px;max-width:640px}@media(max-width:850px){.grid{grid-template-columns:1fr 1fr}}@media(max-width:590px){.nav,.footer-inner{align-items:flex-start;flex-direction:column}.hero{padding:55px 0}.grid,.guide-grid{grid-template-columns:1fr}.body h2{min-height:0}.photo{height:245px}}</style>
</head><body>
<header class="header"><div class="wrap nav"><a class="brand" href="/">GROUP STAY JAPAN</a><nav class="langs" aria-label="Languages">${languageLinks.map(({ locale: item, href }) => `<a href="${href}"${item.code === locale.code ? ' aria-current="page"' : ''}>${item.label}</a>`).join('')}</nav></div></header>
<main><section class="hero"><div class="wrap"><div class="eyebrow">${escapeHtml(locale.eyebrow)}</div><h1>${escapeHtml(locale.h1)}</h1><p class="lead">${escapeHtml(locale.lead)}</p><span class="count">${escapeHtml(locale.count)}</span></div></section>
<section class="content"><div class="wrap"><div class="section-head"><h2>${escapeHtml(locale.listTitle)}</h2><p>${escapeHtml(locale.note)}</p></div><div class="grid">${cards}</div></div></section>
<section class="guide"><div class="wrap"><h2>${escapeHtml(locale.guideTitle)}</h2><div class="guide-grid">${locale.guides.map(([title, text], index) => `<div class="tip"><b>0${index + 1} · ${escapeHtml(title)}</b><p>${escapeHtml(text)}</p></div>`).join('')}</div></div></section>
<section class="faq"><div class="wrap"><h2>${escapeHtml(locale.faqTitle)}</h2>${locale.faqs.map(([question, answer]) => `<details><summary>${escapeHtml(question)}</summary><p>${escapeHtml(answer)}</p></details>`).join('')}</div></section></main>
<footer class="footer"><div class="wrap footer-inner"><div><a href="/">${escapeHtml(locale.back)}</a><p class="small">${escapeHtml(locale.disclaimer)}</p></div><a href="/?city=tokyo&guests=6">${escapeHtml(locale.home)} →</a></div></footer>
</body></html>`;
}

for (const locale of Object.values(locales)) {
  const directory = path.join(root, ...locale.dir.split('/'));
  fs.mkdirSync(directory, { recursive: true });
  fs.writeFileSync(path.join(directory, 'index.html'), renderPage(locale), 'utf8');
}

const staticUrls = ['/', '/_SYSTEM/about.html', '/_SYSTEM/partners.html', ...Object.values(locales).map((locale) => `/${locale.dir}/`)];
const lastmod = new Date().toISOString().slice(0, 10);
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${staticUrls.map((url) => `  <url><loc>https://groupstayjapan.synthx.jp${url}</loc><lastmod>${lastmod}</lastmod></url>`).join('\n')}\n</urlset>\n`;
fs.writeFileSync(path.join(root, 'sitemap.xml'), sitemap, 'utf8');
fs.writeFileSync(path.join(root, 'robots.txt'), 'User-agent: *\nAllow: /\n\nSitemap: https://groupstayjapan.synthx.jp/sitemap.xml\n', 'utf8');
console.log(`Built ${Object.keys(locales).length} localized SEO pages with ${stays.length} Tokyo stays for six guests.`);
