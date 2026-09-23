// Official room specifications checked 2026-09-16. Keep the review date explicit.
const checked = '2026-09-16';
const sources = {
  east: 'https://mimaruhotels.com/en/hotel/tokyo-station-east/',
  nihombashi: 'https://mimaruhotels.com/en/hotel/suites-tokyo-nihombashi/',
};
const copy = {
  en: {
    title: 'Compare the exact room before booking',
    intro: 'A hotel’s maximum capacity does not apply to every room. These examples distinguish adult capacity, sleeping arrangements and laundry facilities. Room names below match the official English listings.',
    heads: ['Hotel / room', 'Adults / area', 'Sleeping arrangement', 'Bath / laundry'],
    single: 'single beds', bunk: 'bunk bed', loft: 'loft beds', futon: 'futons', bath: 'bathroom', shower: 'shower room', washer: 'In-room washer-dryer', shared: 'No in-room washer-dryer; shared coin laundry',
    source: 'Official room specifications', details: 'View hotel and booking options', review: 'Sources checked',
    six: 'For six adults, do not book a four-adult room that allows two young children without beds. Compare the six-adult room types below. A bunk or loft bed requires climbing; choose a layout that suits everyone in your group.',
    eight: 'For eight adults, a six-adult room plus two young children is not equivalent. The connecting option below supplies eight single beds and two bathrooms. Book the named connecting category; two separate reservations do not guarantee a connecting door.',
    long: 'For a longer stay, compare the room’s laundry facilities rather than the hotel name. The two Station East categories below differ: the family apartment uses shared laundry, while the family suite has an in-room washer-dryer.',
    note: 'Adult capacities shown exclude the separate allowance for children aged six and under without beds. Confirm ages, exact room category, dates and total price before booking. This comparison uses published specifications, not a first-hand stay or a live availability check.',
  },
  ja: {
    title: '予約する客室タイプまで比較する', intro: 'ホテル全体の最大定員と、各客室に泊まれる人数は異なります。大人の定員・寝具・洗濯設備を客室ごとに比較します。客室名は公式英語表記です。',
    heads: ['ホテル・客室', '大人定員・面積', '寝具構成', '浴室・洗濯設備'], single: 'シングルベッド', bunk: '二段ベッド', loft: 'ロフトベッド', futon: '布団', bath: '浴室', shower: 'シャワールーム', washer: '室内洗濯乾燥機あり', shared: '室内洗濯乾燥機なし・共用コインランドリー',
    source: '公式の客室仕様', details: '施設・予約先を確認', review: '出典確認日',
    six: '大人6人なら「大人4人＋添い寝の子ども2人」の客室は選べません。下記の大人6人対応の客室で寝具を比較してください。二段・ロフトベッドは上り下りがあるため、同行者に合う構成を選びます。',
    eight: '大人8人と「大人6人＋添い寝の子ども2人」は別の条件です。下記のコネクティングタイプはシングルベッド8台・浴室2室。通常の客室を2室予約するだけでは、室内の連絡ドアは保証されません。',
    long: '連泊ではホテル単位でなく、予約する客室の洗濯設備を確認します。STATION EASTでも、下記ファミリーアパートメントは共用ランドリー、ファミリースイートは室内洗濯乾燥機という違いがあります。',
    note: '大人定員には、別枠の6歳以下・寝具なしの子どもは含めていません。年齢、客室タイプ、日程、合計料金を予約前に確認してください。公式掲載情報の比較であり、宿泊体験や現在の空室を示すものではありません。',
  },
};
const rooms = [
  {hotel:'MIMARU Tokyo Station East',id:'mimaru-tokyo-station-east',name:'Two-Bedroom Family Apartment',adults:6,area:'47',beds:[['single',4],['bunk',1]],baths:1,shower:0,washer:false,source:'east'},
  {hotel:'MIMARU Tokyo Station East',id:'mimaru-tokyo-station-east',name:'Two-Bedroom Family Suite',adults:6,area:'53',beds:[['single',4],['bunk',1]],baths:1,shower:1,washer:true,source:'east'},
  {hotel:'MIMARU SUITES Tokyo Nihombashi',id:'mimaru-suites-tokyo-nihombashi',name:'Two-Bedroom Family Suite',adults:6,area:'57–59',beds:[['single',2],['loft',2],['futon',2]],baths:1,shower:1,washer:true,source:'nihombashi'},
  {hotel:'MIMARU Tokyo Station East',id:'mimaru-tokyo-station-east',name:'Connecting Two-Bedroom Apartment (8 Single-Beds)',adults:8,area:'82',beds:[['single',8]],baths:2,shower:0,washer:false,source:'east'},
];
export function roomComparison(theme, lang, esc) {
  const t=copy[lang];
  if(!t || !['six','eight','long'].includes(theme)) return '';
  const chosen=rooms.filter(r=>theme==='eight'?r.adults===8:r.adults===6);
  return `<section class="content" id="verified-rooms"><div class="wrap"><h2>${t.title}</h2><p>${t.intro}</p><p>${t[theme]}</p><div style="overflow-x:auto"><table style="width:100%;min-width:650px;border-collapse:collapse;text-align:left"><caption style="text-align:left;padding:12px 0">${t.review}: ${checked}</caption><thead><tr>${t.heads.map(h=>`<th scope="col" style="padding:12px;border-bottom:2px solid #164c39">${h}</th>`).join('')}</tr></thead><tbody>${chosen.map(r=>`<tr><th scope="row" style="padding:14px;border-bottom:1px solid #ccd6d0">${esc(r.hotel)}<br><span style="font-weight:normal">${esc(r.name)}</span><br><a style="text-decoration:underline" href="${sources[r.source]}">${t.source}</a><br><a style="text-decoration:underline" data-stay="${r.id}" href="${lang === "ja" ? "/ja" : ""}/stays/${r.id}/?guests=${theme==='eight'?8:6}&amp;lang=${lang}">${t.details}</a></th><td style="padding:14px;border-bottom:1px solid #ccd6d0">${r.adults} / ${r.area} m²</td><td style="padding:14px;border-bottom:1px solid #ccd6d0">${r.beds.map(([b,n])=>`${t[b]} × ${n}`).join('<br>')}</td><td style="padding:14px;border-bottom:1px solid #ccd6d0">${t.bath} × ${r.baths}${r.shower?`<br>${t.shower} × ${r.shower}`:''}<br>${r.washer?t.washer:t.shared}</td></tr>`).join('')}</tbody></table></div><p>${t.note}</p></div></section>`;
}

// Property-specific editorial block; source specifications rechecked 2026-09-24.
export function propertyRoomGuide(id,lang,esc){
 const t=copy[lang],selected=rooms.filter(r=>r.id===id);
 if(!t||!selected.length)return '';
 const ja=lang==='ja',east=id==='mimaru-tokyo-station-east';
 const decision=ja?(east?'大人6人なら47㎡のアパートメントと53㎡のスイートで寝具構成は同じですが、洗濯設備とシャワールームが異なります。連泊で室内洗濯を重視するならスイートを比較してください。8人なら専用のコネクティング客室を選び、通常客室2室の予約と混同しないでください。':'大人6人の寝具はシングル2台・ロフト2台・布団2組に分かれます。全員が通常のベッドを使いたい場合は適しません。上り下りや床の寝具が同行者に合うかを予約前に確認してください。'):(east?'For six adults, the 47 sqm apartment and 53 sqm suite have the same bed mix, but different laundry and shower facilities. Compare the suite if washing clothes inside your room matters for a longer stay. For eight adults, select the named connecting category: two ordinary room reservations do not guarantee an internal connecting door.':'Six adults share two single beds, two loft beds and two futons. This is not a six-standard-bed layout. Check whether climbing to loft beds and using floor bedding suit your group before choosing it.');
 const rows=selected.map(r=>`<tr><th scope="row" style="padding:12px;border-bottom:1px solid #ccd6d0">${esc(r.name)}</th><td style="padding:12px">${r.adults} / ${r.area} m²</td><td style="padding:12px">${r.beds.map(([b,n])=>`${t[b]} × ${n}`).join('<br>')}</td><td style="padding:12px">${t.bath} × ${r.baths}${r.shower?`<br>${t.shower} × ${r.shower}`:''}<br>${r.washer?t.washer:t.shared}</td></tr>`).join('');
 const prefix=ja?'/ja/tokyo/':'/en/tokyo/';
 return `<section class="section" id="property-room-guide"><h2>${ja?'人数・寝具・洗濯設備で客室を選ぶ':'Choose a room by group size, beds and laundry'}</h2><p>${decision}</p><div style="overflow-x:auto"><table style="width:100%;min-width:580px;text-align:left;border-collapse:collapse"><caption>${ja?'公式客室仕様の確認日':'Room specifications checked'}: 2026-09-24</caption><thead><tr>${t.heads.map(x=>`<th scope="col" style="padding:12px">${x}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div><p>${t.note}</p><p><a style="text-decoration:underline" href="${sources[selected[0].source]}">${t.source}</a></p><nav aria-label="${ja?'関連する客室比較':'Related room comparisons'}"><a style="text-decoration:underline" href="${prefix}${ja?'6-guests/':'hotels-for-6-guests/'}">${ja?'東京・大人6人の客室を比較':'Compare Tokyo rooms for six adults'}</a> · <a style="text-decoration:underline" href="${prefix}${ja?'long-stay-apartment-hotels/':'apartment-hotels-for-longer-stays/'}">${ja?'長期滞在と洗濯設備を比較':'Compare laundry options for longer stays'}</a></nav></section>`;
}
