async function fetchSummary(a, b, c, d) {
  const resp = await fetch(`/api/costs/summary?start=${a}&end=${b}&cmp_start=${c}&cmp_end=${d}`);
  return resp.json();
}

function getPeriod(name) {
  const today = new Date();
  let start;
  switch(name) {
    case 'week': start = new Date(today.getFullYear(), today.getMonth(), today.getDate()-7); break;
    case 'month': start = new Date(today.getFullYear(), today.getMonth()-1, today.getDate()); break;
    case 'quarter': start = new Date(today.getFullYear(), today.getMonth()-3, today.getDate()); break;
    case 'year': start = new Date(today.getFullYear(),0,1); break;
  }
  return { start: start.toISOString().slice(0,10), end: today.toISOString().slice(0,10) };
}

let pieChart, compareChart, currentData;

async function updateAll(a,b,c,d) {
  const data = await fetchSummary(a,b,c,d);
  const A = data.periodA, B = data.periodB;
  document.getElementById('sumA').textContent = A.total.toLocaleString() + ' zł';
  document.getElementById('sumB').textContent = B.total.toLocaleString() + ' zł';
  const diff = A.total - B.total;
  document.getElementById('diffAB').textContent = (diff>=0?'+':'') + diff.toLocaleString() + ' zł';
  document.getElementById('pctAB').textContent = B.total>0 ? Math.round(diff/B.total*100)+' %' : (A.total>0?'100 %':'0 %');

  // Prepare categories union
  const cats = {};
  A.categories.forEach(c => cats[c.name] = {name:c.name, A:c.amount, B:0, sub:c.sub});
  B.categories.forEach(c => { cats[c.name] = cats[c.name]||{name:c.name, A:0, B:0, sub:[]}; cats[c.name].B = c.amount; });

  const labels = Object.values(cats).map(c => c.name);
  const valuesA = labels.map(n => cats[n].A);
  const valuesB = labels.map(n => cats[n].B);

  pieChart.data.labels = labels;
  pieChart.data.datasets[0].data = valuesA;
  pieChart.update();

  compareChart.data.labels = labels;
  compareChart.data.datasets[0].data = valuesA;
  compareChart.data.datasets[1].data = valuesB;
  compareChart.update();

  currentData = Object.values(cats);
  filterAndRenderTable();
}

function filterAndRenderTable() {
  const term = document.getElementById('searchInput').value.toLowerCase();
  const tbody = document.getElementById('detailsTable');
  tbody.innerHTML = '';
  currentData.filter(c => c.name.toLowerCase().includes(term)).forEach((c, i) => {
    const rowMain = document.createElement('tr');
    const idx = 'row'+i;
    rowMain.innerHTML = `
      <td><button class="btn btn-sm btn-link" type="button" data-bs-toggle="collapse" data-bs-target="#${idx}">${c.name}</button></td>
      <td>${c.A.toLocaleString()} zł</td>
      <td>${c.B.toLocaleString()} zł</td>
      <td>${(c.A-c.B).toLocaleString()} zł</td>`;
    tbody.appendChild(rowMain);
    const rowSub = document.createElement('tr');
    rowSub.classList.add('collapse');
    rowSub.id = idx;
    rowSub.innerHTML = '<td colspan="4"><ul class="mb-0 ps-4">' +
      c.sub.map(s=>`<li>${s.name}: ${s.amount.toLocaleString()} zł</li>`).join('') +
      '</ul></td>';
    tbody.appendChild(rowSub);
  });
}

document.querySelectorAll('[data-period]').forEach(btn => {
  btn.addEventListener('click', () => {
    const {start,end} = getPeriod(btn.dataset.period);
    document.getElementById('startDate').value = start;
    document.getElementById('endDate').value = end;
    document.getElementById('cmpStartDate').value = start;
    document.getElementById('cmpEndDate').value = end;
  });
});
document.getElementById('filterBtn').addEventListener('click', () => {
  const a = document.getElementById('startDate').value;
  const b = document.getElementById('endDate').value;
  const c = document.getElementById('cmpStartDate').value;
  const d = document.getElementById('cmpEndDate').value;
  updateAll(a,b,c,d);
});
document.getElementById('searchInput').addEventListener('input', filterAndRenderTable);



window.addEventListener('DOMContentLoaded', () => {
  const today = new Date();
  // Period A: last 30 days
  const endA = today;
  const startA = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
  // Period B: 30-60 days ago
  const endB = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
  const startB = new Date(today.getTime() - 60 * 24 * 60 * 60 * 1000);

  const fmt = d => d.toISOString().slice(0,10);
  document.getElementById('startDate').value    = fmt(startA);
  document.getElementById('endDate').value      = fmt(endA);
  document.getElementById('cmpStartDate').value = fmt(startB);
  document.getElementById('cmpEndDate').value   = fmt(endB);

  const ctx1 = document.getElementById('pieChart').getContext('2d');
  pieChart = new Chart(ctx1, {
    type: 'doughnut',
    data: {
      labels: [],
      datasets: [{ data: [], backgroundColor: ['#0d6efd','#198754','#ffc107','#dc3545','#6f42c1'] }]
    },
    options: { cutout: '60%', responsive: true }
  });
  const ctx2 = document.getElementById('compareChart').getContext('2d');
  compareChart = new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [
        { label: 'A', data: [], backgroundColor: '#0d6efd' },
        { label: 'B', data: [], backgroundColor: '#6c757d' }
      ]
    },
    options: { responsive: true, scales: { y: { beginAtZero: true } } }
  });

  updateAll(fmt(startA), fmt(endA), fmt(startB), fmt(endB));
});
