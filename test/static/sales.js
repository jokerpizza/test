$(document).ready(function() {
  const table = $('#salesTable').DataTable({
    ajax: { url: '/api/sales', dataSrc: '' },
    columns: [
      { data: 'date' },
      { data: 'gotowka' },
      { data: 'przelew' },
      { data: 'zaplacono' },
      { data: 'sum' },
      { data: 'id', render: function(id) {
          return `
            <button class="btn btn-sm btn-outline-primary edit-btn" data-id="${id}">✏️</button>
            <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${id}">🗑️</button>`;
        }}
    ],
    dom: 'Bfrtip',
    buttons: ['csvHtml5', 'excelHtml5']
  });

  // Search filter
  $('#searchInput').on('keyup', function() {
    table.search(this.value).draw();
  });

  // Load metrics
  function loadMetrics() {
    fetch('/api/sales/metrics').then(res => res.json()).then(data => {
      $('#metric-daily').text(data.daily);
      $('#metric-weekly').text(data.weekly);
      $('#metric-monthly').text(data.monthly);
    });
  }
  loadMetrics();

  // Modal setup
  const saleModal = new bootstrap.Modal($('#saleModal'));
  $('#addSaleBtn').on('click', () => {
    $('#saleForm')[0].reset();
    $('#saleId').val('');
    $('#saleModalLabel').text('Nowa sprzedaż');
    saleModal.show();
  });

  // Edit button
  $('#salesTable tbody').on('click', '.edit-btn', function() {
    const id = $(this).data('id');
    $.getJSON(`/api/sales`, data => {
      const s = data.find(x => x.id === id);
      if (s) {
        $('#saleId').val(s.id);
        $('#saleDate').val(s.date);
        $('#saleGot').val(s.gotowka);
        $('#salePrz').val(s.przelew);
        $('#saleZap').val(s.zaplacono);
        $('#saleModalLabel').text('Edytuj sprzedaż');
        saleModal.show();
      }
    });
  });

  // Delete button
  $('#salesTable tbody').on('click', '.delete-btn', function() {
    const id = $(this).data('id');
    if (confirm('Usunąć sprzedaż?')) {
      fetch(`/api/sales/${id}`, {method:'DELETE'}).then(() => {
        table.ajax.reload();
        loadMetrics();
      });
    }
  });

  // Form submit for add/edit
  $('#saleForm').on('submit', function(e) {
    e.preventDefault();
    const id = $('#saleId').val();
    const payload = {
      date: $('#saleDate').val(),
      gotowka: $('#saleGot').val(),
      przelew: $('#salePrz').val(),
      zaplacono: $('#saleZap').val()
    };
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/sales/${id}` : '/api/sales';
    $.ajax({
      url, method, contentType:'application/json', data: JSON.stringify(payload)
    }).always(() => {
      saleModal.hide();
      table.ajax.reload();
      loadMetrics();
    });
  });
});
