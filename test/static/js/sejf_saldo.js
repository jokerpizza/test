// Fetch and render sejf data
async function fetchSafeData(start, end) {
  const res = await fetch(`/api/sejf_saldo/summary?start=${start}&end=${end}`);
  return res.json();
}

async function updateSafe(start, end) {
  const data = await fetchSafeData(start, end);
  document.getElementById('currentBalance').textContent = data.currentBalance.toLocaleString() + ' zł';
  document.getElementById('totalDeposits').textContent = data.deposits.toLocaleString() + ' zł';
  document.getElementById('totalWithdrawals').textContent = data.withdrawals.toLocaleString() + ' zł';
  balanceChart.data.labels = data.history.map(d => d.date);
  balanceChart.data.datasets[0].data = data.history.map(d => d.balance);
  balanceChart.update();
  const tbody = document.getElementById('txTable');
  tbody.innerHTML = '';
  data.transactions.forEach(t => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${t.date}</td><td>${t.type}</td><td>${t.amount.toLocaleString()} zł</td><td>${t.balanceAfter.toLocaleString()} zł</td><td>${t.user}</td>`;
    tbody.appendChild(tr);
  });
}

async function initSejf() {
  const today = new Date();
  const start = new Date(today.getTime() - 30*24*60*60*1000);
  const fmt = d => d.toISOString().slice(0,10);
  document.getElementById('filterStart').value = fmt(start);
  document.getElementById('filterEnd').value = fmt(today);
  const ctx = document.getElementById('balanceChart').getContext('2d');
  window.balanceChart = new Chart(ctx, {type:'line', data:{labels:[],datasets:[{label:'Saldo',data:[],fill:true,tension:0.3}]}, options:{responsive:true,maintainAspectRatio:false}});
  document.getElementById('filterBtn').addEventListener('click', e => {e.preventDefault(); updateSafe(document.getElementById('filterStart').value, document.getElementById('filterEnd').value);});
  updateSafe(fmt(start), fmt(today));
}
window.addEventListener('DOMContentLoaded', initSejf);
