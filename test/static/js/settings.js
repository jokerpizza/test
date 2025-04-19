// Ładowanie progów alertów
async function loadThresholds() {
  const res = await fetch('/api/settings/thresholds');
  const data = await res.json();
  const tbody = document.getElementById('thresholdsTable');
  tbody.innerHTML = '';
  data.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.type}</td>
      <td>${item.value.toLocaleString()} zł</td>
      <td>
        <button class="btn btn-sm btn-outline-secondary edit-btn" data-id="${item.id}"><i class="bi bi-pencil"></i></button>
        <button class="btn btn-sm btn-outline-danger del-btn" data-id="${item.id}"><i class="bi bi-trash"></i></button>
      </td>`;
    tbody.appendChild(tr);
  });
}

document.addEventListener('DOMContentLoaded', loadThresholds);
