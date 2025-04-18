
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
      });
  }

  function renderFilters(data) {
    const uniqueCategories = [...new Set(data.map(c => c.main_category).filter(Boolean))];
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
      const byCat = categoryFilter.value === '' || c.main_category === categoryFilter.value;
      const byPay = paymentFilter.value === '' || c.payment_method === paymentFilter.value;
      const byMonth = monthFilter.value === '' || c.date.slice(0, 7) === monthFilter.value;
      return byCat && byPay && byMonth;
    });

    const table = document.createElement('table');
    table.className = 'table table-striped';
    table.innerHTML = `
      <thead>
        <tr>
          <th>Data</th>
          <th>Kategoria główna</th>
          <th>Podkategoria</th>
          <th>Opis</th>
          <th>Kwota</th>
          <th>Płatność</th>
        </tr>
      </thead>
      <tbody>
        ${filtered.map(c => `
          <tr>
            <td>${c.date}</td>
            <td>${c.main_category || '-'}</td>
            <td>${c.subcategory || '-'}</td>
            <td>${c.description}</td>
            <td>${c.amount.toFixed(2)} zł</td>
            <td>${c.payment_method}</td>
          </tr>
        `).join('')}
      </tbody>
    `;
    container.appendChild(table);

    total = filtered.reduce((sum, c) => sum + c.amount, 0);
    summary.textContent = total.toFixed(2);
  }

  document.getElementById('exportCsv').addEventListener('click', () => {
    const headers = ["Data", "Kategoria", "Podkategoria", "Opis", "Kwota", "Płatność"];
    const rows = costs.map(c => [c.date, c.main_category, c.subcategory, c.description, c.amount, c.payment_method]);
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
