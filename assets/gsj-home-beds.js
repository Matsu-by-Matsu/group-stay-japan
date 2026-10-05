(()=>{'use strict';
const grid=document.querySelector('#grid');if(!grid)return;
const langNow=()=>document.querySelector('#lang')?.value||'en';
const guide={en:n=>`/en/tokyo/hotels-for-${n}-guests/`,ja:n=>`/ja/tokyo/${n}-guests/`,'zh-TW':n=>`/zh-tw/tokyo/${n}-guests/`,ko:n=>`/ko/tokyo/${n}-guests/`};
const links=()=>{const f=guide[langNow()]||guide.en;document.querySelectorAll('[data-home-beds-guide]').forEach(a=>a.setAttribute('href',f(a.dataset.homeBedsGuide)));};
const T={
 en:{yes:(q,k)=>(q===2?'Both guests in real beds: ':`All ${q} in real beds: `)+(k===1?'1 room type':`${k} room types`),
     none:q=>q===2?'No room type gives both guests a real bed':`No room type gives all ${q} a real bed`,
     check:q=>q===2?'Check the official site to see if both guests get a real bed':`Check the official site to see if all ${q} get a real bed`,
     bundle:q=>`No single room sleeps ${q}. The listed maximum is for renting several rooms together`},
 ja:{yes:(q,k)=>`${q}人全員がベッドで寝られる客室：${k}室`,none:q=>`${q}人全員がベッドで寝られる客室はありません`,check:q=>`${q}人全員がベッドで寝られるかは、公式サイトで寝具を確認してください`,bundle:q=>`1室で${q}人が泊まれる客室はありません。掲載上の最大定員は、複数の客室をまとめた貸切の人数です`},
 'zh-TW':{yes:(q,k)=>`${q}人全都有床可睡的房型：${k}種`,none:q=>`沒有可讓${q}人全都睡床的房型`,check:q=>`${q}人是否全都有床可睡，請至官方網站確認床型`,bundle:q=>`沒有可供${q}人同住一間的房型。刊載的最多入住人數為多間客房合併包租的人數`},
 ko:{yes:(q,k)=>`${q}명 모두 침대에서 잘 수 있는 객실: ${k}개`,none:q=>`${q}명 모두 침대에서 잘 수 있는 객실은 없습니다`,check:q=>`${q}명 모두 침대에서 잘 수 있는지는 공식 사이트에서 침대 구성을 확인하세요`,bundle:q=>`${q}명이 한 객실에 묵을 수 있는 객실은 없습니다. 표시된 최대 정원은 여러 객실을 묶은 전체 대여 기준입니다`}
};
links();addEventListener('gsj-language',links);
fetch('/assets/gsj-home-beds.json?v=20261005').then(r=>r.json()).then(data=>{
 const update=()=>{
  const t=T[langNow()]||T.en,q=Number(document.querySelector('#guests')?.value||3);
  grid.querySelectorAll('.card[data-id]').forEach(card=>{
   card.querySelectorAll('.gsj-home-beds-card').forEach(p=>p.remove());
   const rooms=data.properties[card.dataset.id],facts=card.querySelector('.facts');if(!rooms||!facts)return;
   const fit=rooms.filter(r=>r[0]>=q);let kind,line;
   if(!fit.length){kind='bundle';line=t.bundle(q);}
   else{const k=fit.filter(r=>r[1]!==null&&r[1]>=q).length,a=fit.filter(r=>r[1]===null).length;
    if(k>=1){kind='yes';line=t.yes(q,k);}else if(a===0){kind='none';line=t.none(q);}else{kind='check';line=t.check(q);}}
   const p=document.createElement('p');p.className='gsj-home-beds-card gsj-home-beds-card-'+kind;p.textContent=line;facts.after(p);
  });
 };
 update();addEventListener('gsj-render',update);addEventListener('gsj-language',update);
}).catch(()=>{});
})();
