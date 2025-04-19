async function fetchSummary(start, end) {
  const url = `/api/costs/summary?start=${start}&end=${end}`;
  const resp = await fetch(url);
  return resp.json();
}

function getPeriod(name) {
  const today = new Date();
  let start;
  switch(name) {
    case 'week':
      start = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 7);
      break;
    case 'month':
      start = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
      break;
    case 'quarter':
      start = new Date(today.getFullYear(), today.getMonth() - 3, today.getDate());
      break;
    case 'year':
      start = new Date(today.getFullYear(), 0, 1);
      break;
  }
  return {
    start: start.toISOString().split('T')[0],
    end:   today.toISOString().split('T')[0]
  };
}

async function updateAll(start, end) {
  const data = await fetchSummary(start, end);
  const prev = data.prev;

  document.getElementById('rangeTotal').textContent = data.total + ' zł';
  const diff = data.total - prev.total;
  document.getElementById('compareDiff').textContent = (diff >= 0 ? '+' : '') + diff + ' zł';
  document.getElementById('comparePct').textContent = prev.total > 0
    ? Math.round(diff / prev.total * 100) + ' %'
    : (data.total === 0 ? '0 %' : '–');

  pieChart.data.labels = data.categories.map(c => c.name);
  pieChart.data.datasets[0].data = data.categories.map(c => c.amount);
  pieChart.update();

  compareChart.data.labels = data.categories.map(c => c.name);
  compareChart.data.datasets[0].data = data.categories.map(c => c.amount);
  compareChart.data.datasets[1].data = prev.categories.map(c => c.amount);
  compareChart.update();

  const tbody = document.getElementById('detailsTable');
  tbody.innerHTML = '';
  data.categories.forEach(c => {
    const pcat = prev.categories.find(p => p.name === c.name);
    const prevSum = pcat ? pcat.amount : 0;
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${c.name}</td>
      <td>${c.amount.toLocaleString()} zł</td>
      <td>${prevSum.toLocaleString()} zł</td>`;
    tbody.appendChild(row);
  });
}

document.querySelectorAll('[data-period]').forEach(btn => {
  btn.addEventListener('click', () => {
    const {start, end} = getPeriod(btn.dataset.period);
    document.getElementById('startDate').value = start;
    document.getElementById('endDate').value = end;
    updateAll(start, end);
  });
});

document.getElementById('filterBtn').addEventListener('click', () => {
  const s = document.getElementById('startDate').value;
  const e = document.getElementById('endDate').value;
  updateAll(s, e);
});

let pieChart, compareChart;
window.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().split('T')[0];
  const lastMonth = new Date(new Date().setMonth(new Date().getMonth() - 1))
                      .toISOString().split('T')[0];
  document.getElementById('startDate').value = lastMonth;
  document.getElementById('endDate').value   = today;

  const ctx1 = document.getElementById('pieChart').getContext('2d');
  pieChart = new Chart(ctx1, {
    type: 'doughnut',
    data:   { labels: [], datasets: [{ data: [], backgroundColor: ['#0d6efd','#198754','#ffc107','#dc3545','#6f42c1'] }] },
    options:{ cutout: '60%', responsive: true }
  });

  const ctx2 = document.getElementById('compareChart').getContext('2d');
  compareChart = new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [
        { label: 'Aktualny',   data: [], backgroundColor: '#0d6efd' },
        { label: 'Poprzedni', data: [], backgroundColor: '#6c757d' }
      ]
    },
    options: { responsive: true, scales: { y: { beginAtZero: true } } }
  });

  updateAll(lastMonth, today);
});
