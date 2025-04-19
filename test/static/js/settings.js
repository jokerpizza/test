document.addEventListener('DOMContentLoaded', () => {
  // load categories
  if(typeof loadCategories==='function') loadCategories();
  // load thresholds
  fetch('/api/settings/thresholds')
    .then(r=>r.json())
    .then(data=>{
      const tb=document.getElementById('thresholdsTable');
      tb.innerHTML='';
      data.forEach(x=>tb.innerHTML+=`<tr><td>${x.type}</td><td>${x.value}</td><td><button class="btn btn-sm btn-outline-danger del" data-id="${x.id}">Usuń</button></td></tr>`);
    });
  // add threshold
  document.getElementById('addThresholdBtn').addEventListener('click', async ()=>{
    const type=prompt('Klucz alertu (np. min_balance)');
    const value=prompt('Wartość progu (zł)');
    if(type&&value){
      await fetch('/api/settings/thresholds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type,value:+value})});
      location.reload();
    }
  });
});