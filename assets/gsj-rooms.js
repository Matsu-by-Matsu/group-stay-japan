(()=>{'use strict';
const node=document.getElementById('gsj-page-data'),data=node?JSON.parse(node.textContent):{},q=new URLSearchParams(location.search);
if(data.id&&['en','ja'].includes(q.get('lang'))&&q.get('lang')!==data.lang){const u=new URL((q.get('lang')==='ja'?'/ja':'')+'/stays/'+data.id+'/',location.origin);u.search=location.search;u.hash=location.hash;location.replace(u.href);return;}
const input=id=>document.getElementById(id), ci=input('checkIn'),co=input('checkOut'),guests=input('guests'),room=input('room-type');
function nights(){return ci&&co?Math.max(0,Math.round((Date.parse(co.value)-Date.parse(ci.value))/86400000)):Number(q.get('nights'))||0}
function selected(){return data.rooms?.find(r=>r.key===room?.value)}
function params(extra={}){return Object.assign({property_id:data.id||'',room_type:selected()?.name||'',guests:Number(guests?.value||q.get('guests'))||0,nights:nights(),page_type:q.get('from')||data.pageType||'property',stay_level:selected()?.level||0},extra)}
function track(name,extra){try{window.GSJTracking?.event(name,params(extra))}catch(_){}}
if(ci&&co){const today=new Date();const day=n=>new Date(today.getTime()+n*86400000).toISOString().slice(0,10);ci.value=q.get('checkIn')||q.get('checkin')||day(14);co.value=q.get('checkOut')||q.get('checkout')||day(16);ci.min=day(0);if(guests)guests.value=String(Math.max(1,Math.min(Number(q.get('guests'))||4,Number(guests.max)||99)));if(room&&q.has('room'))room.value=q.get('room');if(room&&!selected())room.selectedIndex=0;}
function update(){const r=selected();if(guests&&r?.capacity)guests.max=r.capacity;const valid=(!ci||!co||co.value>ci.value)&&(!r||Number(guests.value)<=r.capacity);if(input('booking-error'))input('booking-error').textContent=valid?'':data.lang==='ja'?'日付と選択客室の定員を確認してください。':'Check dates and the selected room capacity.';return valid}
[ci,co,guests,room].filter(Boolean).forEach(x=>x.addEventListener('change',()=>{update();track('room_selection')}));
function bookingURL(){const u=new URL(data.partner);const values={checkIn:ci?.value,checkOut:co?.value,guests:guests?.value,rooms:input('room-count')?.value};for(const [field,param] of Object.entries(data.bookingParameters||{})){if(values[field]&&typeof param==='string')u.searchParams.set(param,values[field]);}return u;}
document.querySelectorAll('[data-affiliate-link]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();if(!update())return;track('affiliate_click');window.open(bookingURL().href,'_blank','noopener');}));
input('booking')?.addEventListener('submit',e=>{e.preventDefault();if(!update())return;track('affiliate_click');const u=bookingURL();window.open(u.href,'_blank','noopener');});
input('stay-duration')?.addEventListener('change',e=>{const n=Number(e.target.value);if(ci&&co&&n){co.value=new Date(Date.parse(ci.value)+n*86400000).toISOString().slice(0,10);update()}track('stay_filter',{nights:n});});
document.querySelectorAll('[data-level-filter]').forEach(s=>s.addEventListener('change',()=>{const level=Number(s.value);const scope=s.closest('.gsj-v31')||document;let count=0;scope.querySelectorAll('tr[data-stay-level]').forEach(row=>{row.hidden=Number(row.dataset.stayLevel)<level;if(!row.hidden)count++});const status=scope.querySelector('[data-filter-count]');if(status)status.textContent=String(count);track('stay_filter',{stay_level:level});}));
document.querySelectorAll('a[data-room-link]').forEach(a=>{const u=new URL(a.href);for(const k of ['checkIn','checkOut','guests','nights'])if(q.has(k))u.searchParams.set(k,q.get(k));a.href=u.href;});
if(data.id)track('property_view');update();
})();
