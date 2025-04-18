
document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.querySelector("#costs-table tbody");
  const filterFrom = document.getElementById("filter-from");
  const filterTo = document.getElementById("filter-to");
  const filterCategory = document.getElementById("filter-category");
  const filterSubcategory = document.getElementById("filter-subcategory");
  const addCostForm = document.getElementById("add-cost-form");

  let categories = [];

  function fetchCategories() {
    return fetch("/api/categories")
      .then(res => res.json())
      .then(data => {
        categories = data;
        populateCategoryFilters();
        populateFormCategories();
      });
  }

  function populateCategoryFilters() {
    categories.forEach(cat => {
      const opt = document.createElement("option");
      opt.value = cat.name;
      opt.textContent = cat.name;
      filterCategory.appendChild(opt);
    });
  }

  function populateFormCategories() {
    const catSelect = addCostForm.category;
    const subSelect = addCostForm.subcategory;
    catSelect.innerHTML = "";
    subSelect.innerHTML = "";

    categories.forEach(cat => {
      const opt = document.createElement("option");
      opt.value = cat.name;
      opt.textContent = cat.name;
      catSelect.appendChild(opt);
    });

    catSelect.addEventListener("change", () => {
      const selected = categories.find(c => c.name === catSelect.value);
      subSelect.innerHTML = "";
      if (selected?.subcategories) {
        selected.subcategories.forEach(sub => {
          const opt = document.createElement("option");
          opt.value = sub.name;
          opt.textContent = sub.name;
          subSelect.appendChild(opt);
        });
      }
    });

    catSelect.dispatchEvent(new Event("change"));
  }

  function loadCosts() {
    let url = "/api/costs";
    const params = new URLSearchParams();
    if (filterFrom.value) params.append("from", filterFrom.value);
    if (filterTo.value) params.append("to", filterTo.value);
    if (filterCategory.value) params.append("category", filterCategory.value);
    if (filterSubcategory.value) params.append("subcategory", filterSubcategory.value);
    if ([...params].length) url += "?" + params.toString();

    fetch(url)
      .then(res => res.json())
      .then(data => {
        tableBody.innerHTML = "";
        data.forEach(cost => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${cost.date}</td>
            <td>${cost.category}</td>
            <td>${cost.subcategory}</td>
            <td>${cost.amount} zł</td>
            <td>${cost.method}</td>
            <td>${cost.note || ""}</td>
            <td></td>
          `;
          tableBody.appendChild(tr);
        });
      });
  }

  addCostForm.addEventListener("submit", e => {
    e.preventDefault();
    const formData = new FormData(addCostForm);
    const payload = {
      date: formData.get("date"),
      category: formData.get("category"),
      subcategory: formData.get("subcategory"),
      amount: parseFloat(formData.get("amount")),
      method: formData.get("method"),
      note: formData.get("note"),
    };

    fetch("/api/costs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => {
        if (res.ok) {
          loadCosts();
          bootstrap.Modal.getInstance(document.getElementById("addCostModal")).hide();
          addCostForm.reset();
        }
      });
  });

  [filterFrom, filterTo, filterCategory, filterSubcategory].forEach(input => {
    input.addEventListener("change", loadCosts);
  });

  fetchCategories().then(loadCosts);
});
