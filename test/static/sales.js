$(document).ready(function(){
  const table = $('#salesTable').DataTable({
    ajax: {
      url: '/api/sales',
      dataSrc: ''
    },
    columns: [
      { data: 'id' },
      { data: 'date' },
      { data: 'gotowka', render: d => parseFloat(d).toFixed(2) },
      { data: 'przelew', render: d => parseFloat(d).toFixed(2) },
      { data: 'zaplacono', render: d => parseFloat(d).toFixed(2) },
      { data: null, orderable: false, render: row => 
          `<button class="btn btn-sm btn-outline-secondary edit-btn me-1" data-id="${row.id}">Edytuj</button>
           <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${row.id}">Usuń</button>`
      }
    ],
    initComplete: function(){
      computeMetrics(this.api().data().toArray());
    }
  });

  function computeMetrics(data){
    const today = new Date();
    let sumToday=0, sumWeek=0, sumMonth=0;
    data.forEach(r => {
      const d = new Date(r.date);
      const diffDays = (today - d)/(1000*60*60*24);
      if(d.toDateString()===today.toDateString()){
        sumToday += parseFloat(r.zaplacono);
      }
      if(diffDays>=0 && diffDays<7){
        sumWeek += parseFloat(r.zaplacono);
      }
      if(d.getFullYear()===today.getFullYear() && d.getMonth()===today.getMonth()){
        sumMonth += parseFloat(r.zaplacono);
      }
    });
    $('#todaySum').text(sumToday.toFixed(2));
    $('#weekSum').text(sumWeek.toFixed(2));
    $('#monthSum').text(sumMonth.toFixed(2));
  }

  table.on('xhr', function(){
    const data = table.ajax.json();
    computeMetrics(data);
  });

  // Add sale
  $('#addSaleForm').on('submit', function(e){
    e.preventDefault();
    const payload = {
      date: $('#saleDate').val(),
      gotowka: +$('#saleGot').val(),
      przelew: +$('#salePrz').val(),
      zaplacono: +$('#saleZap').val()
    };
    $.post('/api/sales', JSON.stringify(payload), null, 'json')
      .done(() => {
        $('#addSaleModal').modal('hide');
        table.ajax.reload();
      });
  });

  // Edit sale
  $('#salesTable').on('click', '.edit-btn', function(){
    const id = $(this).data('id');
    $.getJSON('/api/sales/'+id, r => {
      $('#editSaleId').val(r.id);
      $('#editSaleDate').val(r.date);
      $('#editSaleGot').val(r.gotowka);
      $('#editSalePrz').val(r.przelew);
      $('#editSaleZap').val(r.zaplacono);
      $('#editSaleModal').modal('show');
    });
  });
  $('#editSaleForm').submit(function(e){
    e.preventDefault();
    const id=$('#editSaleId').val();
    const payload={ date:$('#editSaleDate').val(), gotowka:+$('#editSaleGot').val(), przelew:+$('#editSalePrz').val(), zaplacono:+$('#editSaleZap').val() };
    $.ajax({url:'/api/sales/'+id, method:'PUT', data:JSON.stringify(payload)})
      .done(()=>{ $('#editSaleModal').modal('hide'); table.ajax.reload(); });
  });

  // Delete sale
  $('#salesTable').on('click', '.delete-btn', function(){
    const id=$(this).data('id');
    if(confirm('Usuń #'+id+'?')){
      $.ajax({url:'/api/sales/'+id, method:'DELETE'})
        .done(()=> table.ajax.reload() );
    }
  });
});