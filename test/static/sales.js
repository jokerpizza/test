document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.querySelector('#salesTable tbody');
  
  async function loadSales() {
    const resp = await fetch('/api/sales');
    const data = await resp.json();
    tableBody.innerHTML = data.map(row => `
      <tr>
        <td>${row.id}</td>
        <td>${row.date}</td>
        <td>${row.gotowka.toFixed(2)}</td>
        <td>${row.przelew.toFixed(2)}</td>
        <td>${row.zaplacono.toFixed(2)}</td>
        <td>
          <button class="btn btn-sm btn-outline-secondary edit-btn me-1" data-id="${row.id}">Edytuj</button>
          <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${row.id}">Usuń</button>
        </td>
      </tr>
    `).join('');
    attachRowEvents();
  }

  async function loadMetrics() {
    const resp = await fetch('/api/sales/metrics');
    const json = await resp.json();
    document.getElementById('todaySum').textContent = json.today.toFixed(2);
    document.getElementById('weekSum').textContent = json.week.toFixed(2);
    document.getElementById('monthSum').textContent = json.month.toFixed(2);
  }

  function attachRowEvents() {
    document.querySelectorAll('.edit-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        const resp = await fetch('/api/sales/' + id);
        const row = await resp.json();
        document.getElementById('editSaleId').value = row.id;
        document.getElementById('editSaleDate').value = row.date;
        document.getElementById('editSaleGot').value = row.gotowka;
        document.getElementById('editSalePrz').value = row.przelew;
        document.getElementById('editSaleZap').value = row.zaplacono;
        new bootstrap.Modal(document.getElementById('editSaleModal')).show();
      });
    });
    document.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        if(confirm('Usunąć sprzedaż #'+btn.dataset.id+'?')) {
          await fetch('/api/sales/' + btn.dataset.id, { method: 'DELETE' });
          loadSales();
          loadMetrics();
        }
      });
    });
  }

  // Add sale
  document.getElementById('addSaleBtn').addEventListener('click', () => {
    new bootstrap.Modal(document.getElementById('addSaleModal')).show();
  });
  document.getElementById('addSaleForm').addEventListener('submit', async e => {
    e.preventDefault();
    const data = {
      date: document.getElementById('saleDate').value,
      gotowka: parseFloat(document.getElementById('saleGot').value),
      przelew: parseFloat(document.getElementById('salePrz').value),
      zaplacono: parseFloat(document.getElementById('saleZap').value)
    };
    await fetch('/api/sales', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(data)
    });
    bootstrap.Modal.getInstance(document.getElementById('addSaleModal')).hide();
    loadSales();
    loadMetrics();
  });

  // Edit sale
  document.getElementById('editSaleForm').addEventListener('submit', async e => {
    e.preventDefault();
    const id = document.getElementById('editSaleId').value;
    const data = {
      date: document.getElementById('editSaleDate').value,
      gotowka: parseFloat(document.getElementById('editSaleGot').value),
      przelew: parseFloat(document.getElementById('editSalePrz').value),
      zaplacono: parseFloat(document.getElementById('editSaleZap').value)
    };
    await fetch('/api/sales/' + id, {
      method: 'PUT',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(data)
    });
    bootstrap.Modal.getInstance(document.getElementById('editSaleModal')).hide();
    loadSales();
    loadMetrics();
  });

  // Initial load
  loadSales();
  loadMetrics();
});