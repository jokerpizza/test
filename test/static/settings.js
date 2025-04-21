document.addEventListener('DOMContentLoaded', () => {
  loadCategories();
  initMainForm();
  initSubForm();
});

async function loadCategories() {
  const res = await fetch('/api/categories');
  const data = await res.json();
  const container = document.getElementById('categories-container');
  container.innerHTML = '';
  data.forEach(mc => {
    const col = document.createElement('div');
    col.className = 'col-md-4';
    col.innerHTML = `
      <div class="card">
        <div class="card-header d-flex justify-content-between">
          <span>${mc.name}</span>
          <div>
            <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditMain(${mc.id}, \`${mc.name}\`)">✏️</button>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteMain(${mc.id})">🗑️</button>
          </div>
        </div>
        <ul class="list-group list-group-flush" id="subs-${mc.id}"></ul>
        <div class="card-body text-center">
          <button class="btn btn-sm btn-secondary" onclick="openAddSub(${mc.id})">+ Podkategoria</button>
        </div>
      </div>`;
    container.appendChild(col);
    const list = col.querySelector(`#subs-${mc.id}`);
    mc.subcategories.forEach(sc => {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex justify-content-between';
      li.textContent = sc.name;
      const actions = document.createElement('div');
      actions.innerHTML = `
        <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditSub(${sc.id}, \`${sc.name}\`)">✏️</button>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteSub(${sc.id})">🗑️</button>`;
      li.appendChild(actions);
      list.appendChild(li);
    });
  });
}

function initMainForm() {
  const modal = new bootstrap.Modal(document.getElementById('mainModal'));
  document.getElementById('mainForm').addEventListener('submit', async e => {
    e.preventDefault();
    const id = document.getElementById('mainId').value;
    const name = document.getElementById('mainName').value.trim();
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/categories/${id}` : '/api/categories';
    await fetch(url, {
      method,
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({name})
    });
    modal.hide();
    loadCategories();
  });
  window.openAddMainModal = () => {
    document.getElementById('mainId').value = '';
    document.getElementById('mainName').value = '';
    modal.show();
  };
  window.openEditMain = (id, name) => {
    document.getElementById('mainId').value = id;
    document.getElementById('mainName').value = name;
    modal.show();
  };
  window.deleteMain = async id => {
    if (confirm('Usunąć kategorię główną?')) {
      await fetch(`/api/categories/${id}`, {method:'DELETE'});
      loadCategories();
    }
  };
}

function initSubForm() {
  const modal = new bootstrap.Modal(document.getElementById('subModal'));
  document.getElementById('subForm').addEventListener('submit', async e => {
    e.preventDefault();
    const id = document.getElementById('subId').value;
    const parent_id = document.getElementById('subParentId').value;
    const name = document.getElementById('subName').value.trim();
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/subcategories/${id}` : '/api/subcategories';
    await fetch(url, {
      method,
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({name, parent_id})
    });
    modal.hide();
    loadCategories();
  });
  window.openAddSub = parent_id => {
    document.getElementById('subId').value = '';
    document.getElementById('subParentId').value = parent_id;
    document.getElementById('subName').value = '';
    new bootstrap.Modal(document.getElementById('subModal')).show();
  };
  window.openEditSub = (id, name) => {
    document.getElementById('subId').value = id;
    document.getElementById('subParentId').value = '';
    document.getElementById('subName').value = name;
    new bootstrap.Modal(document.getElementById('subModal')).show();
  };
  window.deleteSub = async id => {
    if (confirm('Usunąć podkategorię?')) {
      await fetch(`/api/subcategories/${id}`, {method:'DELETE'});
      loadCategories();
    }
  };
}
