(()=>{'use strict';
document.querySelectorAll('[data-beds-filter]').forEach(btn=>{
 const table=btn.closest('.gsj-readiness-table'); if(!table) return;
 btn.addEventListener('click',()=>{
  const on=btn.getAttribute('aria-pressed')!=='true';
  btn.setAttribute('aria-pressed',String(on));
  table.querySelectorAll('tr[data-all-beds]').forEach(tr=>tr.classList.toggle('gsj-beds-hidden',on&&tr.dataset.allBeds!=='1'));
 });
});})();
