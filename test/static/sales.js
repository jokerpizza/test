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
          return '<button class="btn btn-sm btn-danger delete-btn" data-id="'+row.id+'">Usuń</button>';
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

  $('#salesTable').on('click', '.delete-btn', function(){
    const id = $(this).data('id');
    // OTP flow omitted for simplicity
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