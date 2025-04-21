document.addEventListener('DOMContentLoaded', () => {
  const addBtn = document.getElementById('add-item');
  const container = document.getElementById('recipe-items');
  addBtn.addEventListener('click', () => {
    const idx = container.children.length;
    const div = document.createElement('div');
    div.className = 'd-flex mb-2';
    div.innerHTML = `
      <select name="product_id_${idx}" class="form-select me-2" required>
        {% for p in products %}<option value="{{ p.id }}">{{ p.name }}</option>{% endfor %}
      </select>
      <input name="weight_kg_${idx}" type="number" step="0.01" class="form-control me-2" placeholder="kg" required>
    `;
    container.appendChild(div);
  });
});