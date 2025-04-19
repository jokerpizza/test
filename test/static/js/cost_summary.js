async function fetchSummary(a, b, c, d) {
  const url = `/api/costs/summary?start=${a}&end=${b}&cmp_start=${c}&cmp_end=${d}`;
  const resp = await fetch(url);
  return resp.json();
}
function getPeriod(name) { /* same as before */ }
async function updateAll(a, b, c, d) {
  const data = await fetchSummary(a, b, c, d);
  const prev = data.prev;
  /* update cards, charts, table as before */
}
document.querySelectorAll('[data-period]').forEach(btn => {
  btn.addEventListener('click', () => {
    const {start, end} = getPeriod(btn.dataset.period);
    document.getElementById('startDate').value = start;
    document.getElementById('endDate').value = end;
  });
});
document.getElementById('filterBtn').addEventListener('click', () => {
  const a = document.getElementById('startDate').value;
  const b = document.getElementById('endDate').value;
  const c = document.getElementById('compStartDate').value;
  const d = document.getElementById('compEndDate').value;
  updateAll(a, b, c, d);
});
window.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().split('T')[0];
  const lastMonth = new Date(new Date().setMonth(new Date().getMonth()-1)).toISOString().split('T')[0];
  document.getElementById('startDate').value = lastMonth;
  document.getElementById('endDate').value = today;
  document.getElementById('compStartDate').value = lastMonth;
  document.getElementById('compEndDate').value = today;
  updateAll(lastMonth, today, lastMonth, today);
});
