
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('costCardsContainer');
  const summary = document.getElementById('totalAmount');
  const categoryFilter = document.getElementById('filterCategory');
  const paymentFilter = document.getElementById('filterPayment');
  const monthFilter = document.getElementById('filterMonth');

  let costs = [];

  function fetchCosts() {
    fetch('/api/costs')
      .then(res => res.json())
      .then(data => {
        costs = data;
        renderFilters(data);
        renderCosts();
        renderChart();
      });
  }

  function renderFilters(data) {
    const uniqueCategories = [...new Set(data.map(c => c.category))];
    categoryFilter.innerHTML = '<option value="">Wszystkie kategorie</option>';
    uniqueCategories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      categoryFilter.appendChild(opt);
    });
  }

  function renderCosts() {
    container.innerHTML = '';
    let total = 0;

    const filtered = costs.filter(c => {
      const byCat = categoryFilter.value === '' || c.category === categoryFilter.value;
      const byPay = paymentFilter.value === '' || c.payment_method === paymentFilter.value;
      const byMonth = monthFilter.value === '' || c.date.slice(0, 7) === monthFilter.value;
      return byCat && byPay && byMonth;
    });

    filtered.forEach(cost => {
      const col = document.createElement('div');
      col.className = 'col-md-4';
      col.innerHTML = `
        <div class="card mb-3">
          <div class="card-body">
            <h5 class="card-title">${cost.category}</h5>
            <h6 class="card-subtitle mb-2 text-muted">${cost.date}</h6>
            <p class="card-text">${cost.description}</p>
            <p class="fw-bold">${cost.amount.toFixed(2)} zł (${cost.payment_method})</p>
          </div>
        </div>`;
      container.appendChild(col);
      total += cost.amount;
    });

    summary.textContent = total.toFixed(2);
  }

  function renderChart() {
    const ctx = document.getElementById('costChart').getContext('2d');
    const categories = {};
    costs.forEach(c => {
      if (!categories[c.category]) categories[c.category] = 0;
      categories[c.category] += c.amount;
    });

    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: Object.keys(categories),
        datasets: [{
          data: Object.values(categories),
        }]
      }
    });
  }

  document.getElementById('exportCsv').addEventListener('click', () => {
    const headers = ["Data", "Kategoria", "Opis", "Kwota", "Płatność"];
    const rows = costs.map(c => [c.date, c.category, c.description, c.amount, c.payment_method]);
    const csv = [headers, ...rows].map(e => e.join(",")).join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "koszty.csv";
    link.click();
  });

  categoryFilter.addEventListener('change', renderCosts);
  paymentFilter.addEventListener('change', renderCosts);
  monthFilter.addEventListener('change', renderCosts);

  fetchCosts();
});
