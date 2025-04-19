// static/js/cost_summary.js
async function fetchSummary(url) {
  return (await fetch(url)).json();
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
  return { start: start.toISOString().split('T')[0], end: today.toISOString().split('T')[0] };
}
async function updateAll(start, end) {
  const data = await fetchSummary(`/api/costs/summary?start=${start}&end=${end}`);
  const prev = data.prev;
  document.getElementById('rangeTotal').textContent = data.total + ' zł';
  const diff = data.total - prev.total;
  document.getElementById('compareDiff').textContent = (diff > 0 ? '+' : '') + diff + ' zł';
  document.getElementById('comparePct').textContent = prev.total > 0 ? Math.round(diff / prev.total * 100) + '%' : '–';
  costChart.data.labels = data.categories.map(c => c.name);
  costChart.data.datasets[0].data = data.categories.map(c => c.amount);
  costChart.update();
  compareChart.data.labels = data.categories.map(c => c.name);
  compareChart.data.datasets[0].data = data.categories.map(c => c.amount);
  compareChart.data.datasets[1].data = prev.categories.map(c => c.amount);
  compareChart.update();
  const tbody = document.querySelector('#detailsTable tbody');
  tbody.innerHTML = '';
  data.categories.forEach((c, i) => {
    const subPrev = prev.categories.find(p => p.name === c.name)?.sub || [];
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="px-4 py-2">${c.name}</td><td class="px-4 py-2">${c.amount} zł</td><td class="px-4 py-2">${subPrev.reduce((a,s) => a + s.amount, 0)} zł</td>`;
    tbody.appendChild(tr);
  });
}
document.querySelectorAll('.periodBtn').forEach(btn => {
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
let costChart, compareChart;
window.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().split('T')[0];
  const lastMonth = new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString().split('T')[0];
  document.getElementById('startDate').value = lastMonth;
  document.getElementById('endDate').value = today;
  const ctx1 = document.getElementById('pieChart').getContext('2d');
  costChart = new Chart(ctx1, {
    type: 'doughnut',
    data: { labels: [], datasets: [{ data: [], backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'] }] },
    options: { cutout: '50%' }
  });
  const ctx2 = document.getElementById('compareChart').getContext('2d');
  compareChart = new Chart(ctx2, {
    type: 'bar',
    data: { labels: [], datasets: [{ label: 'Aktualny', data: [], backgroundColor: '#2563EB' }, { label: 'Poprzedni', data: [], backgroundColor: '#6B7280' }] },
    options: { responsive: true, scales: { y: { beginAtZero: true } } }
  });
  updateAll(lastMonth, today);
});
