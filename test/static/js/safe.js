// Fetch and render safe data
async function fetchSafeData(start, end) {
  const res = await fetch(`/api/safe/summary?start=${start}&end=${end}`);
  return res.json();
}

async function initSafe() {
  const today = new Date();
  const start = new Date(today.getTime() - 30*24*60*60*1000);
  const fmt = d => d.toISOString().slice(0,10);
  document.getElementById('filterStart').value = fmt(start);
  document.getElementById('filterEnd').value = fmt(today);

  // init chart
  const ctx = document.getElementById('balanceChart').getContext('2d');
  window.balanceChart = new Chart(ctx, {
    type: 'line',
    data: { labels: [], datasets: [{ label:'Saldo', data:[], fill:true, tension:0.3 }] },
    options:{responsive:true,maintainAspectRatio:false}
  });

  document.getElementById('filterBtn').addEventListener('click', async ()=> {
    const a = document.getElementById('filterStart').value;
    const b = document.getElementById('filterEnd').value;
    await updateSafe(a,b);
  });

  await updateSafe(fmt(start), fmt(today));
}

async function updateSafe(start, end) {
  const data = await fetchSafeData(start, end);
  document.getElementById('currentBalance').textContent = data.currentBalance.toLocaleString() + ' zł';
  document.getElementById('totalDeposits').textContent = data.deposits.toLocaleString() + ' zł';
  document.getElementById('totalWithdrawals').textContent = data.withdrawals.toLocaleString() + ' zł';
  // chart
  balanceChart.data.labels = data.history.map(d=>d.date);
  balanceChart.data.datasets[0].data = data.history.map(d=>d.balance);
  balanceChart.update();
  // table
  const tbody = document.getElementById('txTable');
  tbody.innerHTML = '';
  data.transactions.forEach(t => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${t.date}</td><td>${t.type}</td><td>${t.amount.toLocaleString()} zł</td>
      <td>${t.balanceAfter.toLocaleString()} zł</td><td>${t.desc}</td><td>${t.user}</td>`;
    tbody.appendChild(tr);
  });
}

window.addEventListener('DOMContentLoaded', initSafe);
