/*  static/sales.js  */

$(function () {

  /* ---------- tabela sprzedaży ---------- */
  const table = $('#salesTable').DataTable({
    ajax: {
      url: '/api/sales',
      dataSrc: ''
    },
    order: [[0, 'desc']],
    columns: [
      { data: 'date' },
      { data: 'gotowka',  className: 'text-end', render: $.fn.dataTable.render.number(' ', ',', 2, '') },
      { data: 'przelew',  className: 'text-end', render: $.fn.dataTable.render.number(' ', ',', 2, '') },
      { data: 'zaplacono',className: 'text-end fw-bold', render: $.fn.dataTable.render.number(' ', ',', 2, '') },
      {
        data: null,
        orderable: false,
        className: 'text-center',
        render: row => `
          <button class="btn btn-sm btn-outline-primary edit-sale"   data-id="${row.id}"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger  delete-sale" data-id="${row.id}"><i class="bi bi-trash"></i></button>`
      }
    ],
    dom: 'ftipr',
    language: {
      search: 'Szukaj:',
      info: '_TOTAL_ pozycji',
      paginate: { previous: '‹', next: '›' }
    }
  });

  /* ---------- metryki ---------- */
  const loadMetrics = () => {
    $.getJSON('/api/sales/metrics', m => {
      $('#metricToday').text(m.today.toLocaleString('pl-PL', {minimumFractionDigits:2}));
      $('#metricWeek' ).text(m.week .toLocaleString('pl-PL', {minimumFractionDigits:2}));
      $('#metricMonth').text(m.month.toLocaleString('pl-PL', {minimumFractionDigits:2}));
    });
  };
  loadMetrics();

  /* ---------- otwórz modal “Dodaj” ---------- */
  $('#addSaleBtn').on('click', () => {
    $('#saleModalLabel').text('Nowa sprzedaż');
    $('#saleForm')[0].reset();
    $('#saleModal').data('id', null).modal('show');
  });

  /* ---------- zapisz (add / edit) ---------- */
  $('#saveSale').on('click', () => {
    const id  = $('#saleModal').data('id');
    const url = id ? `/api/sales/${id}` : '/api/sales';
    const verb= id ? 'PUT'             : 'POST';

    const payload = {
      date      : $('#saleDate'   ).val(),
      gotowka   : parseFloat($('#saleCash'   ).val()) || 0,
      przelew   : parseFloat($('#saleTransfer').val()) || 0,
      zaplacono : parseFloat($('#salePaid'   ).val()) || 0
    };

    $.ajax({
      url,
      method : verb,
      contentType : 'application/json',
      data        : JSON.stringify(payload),
      success     : () => {
        $('#saleModal').modal('hide');
        table.ajax.reload(null, false);
        loadMetrics();
      }
    });
  });

  /* ---------- usuń ---------- */
  $('#salesTable').on('click', '.delete-sale', function () {
    const id = $(this).data('id');
    if (confirm('Usunąć tę sprzedaż?')) {
      $.ajax({
        url    : `/api/sales/${id}`,
        method : 'DELETE',
        success: () => {
          table.ajax.reload(null, false);
          loadMetrics();
        }
      });
    }
  });

  /* ---------- edytuj ---------- */
  $('#salesTable').on('click', '.edit-sale', function () {
    const id = $(this).data('id');
    $.getJSON(`/api/sales/${id}`, row => {
      $('#saleModalLabel').text('Edytuj sprzedaż');
      $('#saleDate'   ).val(row.date);
      $('#saleCash'   ).val(row.gotowka);
      $('#saleTransfer').val(row.przelew);
      $('#salePaid'   ).val(row.zaplacono);
      $('#saleModal').data('id', id).modal('show');
    });
  });

});
