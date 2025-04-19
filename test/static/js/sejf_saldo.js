// Safe data handling
async function fetchSafeData(start, end){
  const res = await fetch(`/api/sejf_saldo/summary?start=${start}&end=${end}`);
  return res.json();
}
async function loadThresholds(){
  const res = await fetch('/api/settings/thresholds');
  const data = await res.json();
  const tb = document.getElementById('thresholdsTable');
  tb.innerHTML = '';
  data.forEach(t=> {
    tb.innerHTML += `<tr><td>${t.type}</td><td>${t.value}</td><td><button class="btn btn-sm btn-danger del" data-id="${t.id}">Usuń</button></td></tr>`;
  });
}
async function addThreshold(){
  const key = prompt('Typ alertu (np. min_balance)');
  const value = prompt('Wartość progu (zł)');
  if(key && value){
    await fetch('/api/settings/thresholds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:key,value:+value})});
    loadThresholds();
  }
}
async function initSafe(){
  const today=new Date(), start=new Date(today.getTime()-30*24*60*60*1000);
  const fmt=d=>d.toISOString().slice(0,10);
  document.getElementById('filterStart').value=fmt(start);
  document.getElementById('filterEnd').value=fmt(today);
  const ctx=document.getElementById('balanceChart').getContext('2d');
  window.balanceChart=new Chart(ctx,{type:'line',data:{labels:[],datasets:[{label:'Saldo',data:[],fill:true,tension:0.3}]},options:{responsive:true,maintainAspectRatio:false}});
  document.getElementById('filterBtn').addEventListener('click',e=>{e.preventDefault();refreshSafe();});
  document.getElementById('addThresholdBtn').addEventListener('click',addThreshold);
  await loadThresholds();
  refreshSafe();
}
async function refreshSafe(){
  const start=document.getElementById('filterStart').value;
  const end=document.getElementById('filterEnd').value;
  const data=await fetchSafeData(start,end);
  document.getElementById('currentBalance').textContent=data.currentBalance+' zł';
  // chart
  balanceChart.data.labels=data.history.map(h=>h.date);
  balanceChart.data.datasets[0].data=data.history.map(h=>h.balance);
  balanceChart.update();
  // table
  const txTable=document.getElementById('txTable');
  txTable.innerHTML=`<thead><tr><th>Data</th><th>Typ</th><th>Kwota</th><th>Saldo po trans.</th><th>Użytkownik</th></tr></thead><tbody>`;
  data.transactions.forEach(t=>txTable.innerHTML+=`<tr><td>${t.date}</td><td>${t.type}</td><td>${t.amount}</td><td>${t.balanceAfter}</td><td>${t.user}</td></tr>`);
  txTable.innerHTML+='</tbody>';
}
window.addEventListener('DOMContentLoaded',initSafe);
