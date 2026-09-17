import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html=fs.readFileSync(new URL('../_SYSTEM/property.html',import.meta.url),'utf8');
assert.equal((html.match(/booking\.onsubmit=/g)||[]).length,1,'Keep one authoritative booking handler');
for(const match of html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)){
  if(match[1].includes('application/ld+json')) JSON.parse(match[2]);
  else if(match[2].trim())new vm.Script(match[2]);
}
const source=html.slice(html.indexOf('booking.onsubmit=')).split('</script>')[0];
for(const language of ['en','ja','ko','zh-TW'])for(const mode of ['tracking','fallback','missing','throws','invalid']){
  const events=[], opened=[];
  const ctx={URL,Number,language,propertyId:'test-hotel',property:{name:'Test hotel'},
    guests:{value:'6'},checkIn:{value:'2026-10-01'},checkOut:{value:mode==='invalid'?'2026-09-30':'2026-10-03'},
    nights:()=>2,error:{textContent:''},booking:{dataset:{partnerUrl:'https://jp.trip.com/hotels/test/?Allianceid=10118837&SID=328695221&trip_sub1=test-hotel&trip_sub3=test-tracking'}},
    tripLocaleHost:lang=>({en:'www.trip.com',ja:'jp.trip.com',ko:'kr.trip.com','zh-TW':'tw.trip.com'})[lang],
    window:{open:(...args)=>opened.push(args)},console:{warn:()=>{}}};
  if(mode==='tracking'||mode==='invalid')ctx.window.GSJTracking={event:(...args)=>events.push(args)};
  if(mode==='fallback')ctx.gtag=(prefix,...args)=>{assert.equal(prefix,'event');events.push(args)};
  if(mode==='throws')ctx.window.GSJTracking={event:()=>{throw Error('Simulated analytics failure')}};
  vm.runInNewContext(source,ctx);let prevented=false;ctx.booking.onsubmit({preventDefault:()=>{prevented=true}});
  assert.ok(prevented);
  if(mode==='invalid'){assert.equal(events.length,0);assert.equal(opened.length,0);assert.ok(ctx.error.textContent);continue}
  assert.equal(opened.length,1);const url=new URL(opened[0][0]);
  assert.equal(url.hostname,ctx.tripLocaleHost(language));
  for(const [key,value] of Object.entries({Allianceid:'10118837',SID:'328695221',trip_sub1:'test-hotel',trip_sub3:'test-tracking',checkIn:'2026-10-01',checkOut:'2026-10-03',adult:'6'}))assert.equal(url.searchParams.get(key),value);
  assert.equal(events.length,['tracking','fallback'].includes(mode)?1:0);
  if(events.length){assert.equal(events[0][0],'affiliate_click');assert.equal(events[0][1].guests,6);assert.equal(events[0][1].language,language);assert.equal(events[0][1].nights,2)}
}
console.log('PASS: 20 booking cases; one event, locale/date/guest/tracking preservation, invalid dates, analytics failure isolation. GA4 network delivery is not tested.');
