$(document).ready(function(){
  const table = $('#salesTable').DataTable({
    ajax: {
      url: '/api/sales',
      dataSrc: ''
    },
    columns: [
      { data: 'id' },
      { data: 'date' },
      { data: 'gotowka' },
      { data: 'przelew' },
      { data: 'zaplacono' },
      { data: null, render: function(row){
          return '<button class="btn btn-sm btn-warning edit-btn me-1" data-id="'+row.id+'">Edytuj</button>' +
                 '<button class="btn btn-sm btn-danger delete-btn" data-id="'+row.id+'">Usuń</button>';
        }
      }
    ]
  });

  function loadMetrics(){
    $.getJSON('/api/sales/metrics', function(json){
      $('#todaySum').text(json.today.toFixed(2));
      $('#weekSum').text(json.week.toFixed(2));
      $('#monthSum').text(json.month.toFixed(2));
    });
  }

  loadMetrics();

  // Add sale
  $('#addSaleForm').on('submit', function(e){
    e.preventDefault();
    const data = {
      date: $('#saleDate').val(),
      gotowka: parseFloat($('#saleGot').val()),
      przelew: parseFloat($('#salePrz').val()),
      zaplacono: parseFloat($('#saleZap').val())
    };
    $.ajax({
      url: '/api/sales',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(data)
    }).done(function(){
      $('#addSaleModal').modal('hide');
      table.ajax.reload();
      loadMetrics();
    }).fail(function(){
      alert('Błąd przy dodawaniu sprzedaży');
    });
  });

  // Edit sale - open modal
  $('#salesTable').on('click', '.edit-btn', function(){
    const id = $(this).data('id');
    $.getJSON('/api/sales/' + id, function(row){
      $('#editSaleId').val(row.id);
      $('#editSaleDate').val(row.date);
      $('#editSaleGot').val(row.gotowka);
      $('#editSalePrz').val(row.przelew);
      $('#editSaleZap').val(row.zaplacono);
      $('#editSaleModal').modal('show');
    });
  });

  // Update sale
  $('#editSaleForm').on('submit', function(e){
    e.preventDefault();
    const id = $('#editSaleId').val();
    const data = {
      date: $('#editSaleDate').val(),
      gotowka: parseFloat($('#editSaleGot').val()),
      przelew: parseFloat($('#editSalePrz').val()),
      zaplacono: parseFloat($('#editSaleZap').val())
    };
    $.ajax({
      url: '/api/sales/' + id,
      method: 'PUT',
      contentType: 'application/json',
      data: JSON.stringify(data)
    }).done(function(){
      $('#editSaleModal').modal('hide');
      table.ajax.reload();
      loadMetrics();
    }).fail(function(){
      alert('Błąd przy aktualizacji sprzedaży');
    });
  });

  // Delete sale
  $('#salesTable').on('click', '.delete-btn', function(){
    const id = $(this).data('id');
    if(confirm('Usunąć sprzedaż #'+id+'?')){
      $.ajax({
        url: '/api/sales/' + id,
        method: 'DELETE'
      }).done(function(){
        table.ajax.reload();
        loadMetrics();
      });
    }
  });
});