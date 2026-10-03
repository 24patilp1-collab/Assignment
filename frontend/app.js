const API = "/api/employees";
const form = document.getElementById("emp-form");
const body = document.getElementById("emp-body");
const msg = document.getElementById("message");
const searchInput = document.getElementById("search-input");
const searchField = document.getElementById("search-field");
const submitBtn = document.getElementById("submit-btn");
const cancelBtn = document.getElementById("cancel-btn");
const formTitle = document.getElementById("form-title");
let editingId = null;

// ---------- client-side validation (mirrors server rules) ----------
const rules = {
  emp_id: v => /^[A-Za-z0-9-]{1,20}$/.test(v) || "1-20 letters, digits or hyphens",
  name: v => /^[A-Za-z][A-Za-z .'-]{1,99}$/.test(v) || "2-100 letters only",
  department: v => (v.length >= 1 && v.length <= 60) || "Department is required",
  designation: v => (v.length >= 1 && v.length <= 60) || "Designation is required",
  salary: v => (/^\d+(\.\d{1,2})?$/.test(v) && parseFloat(v) > 0) || "Positive number, max 2 decimals",
  contact: v => /^[6-9]\d{9}$/.test(v) || "10-digit Indian mobile number",
};

function showErrors(errors) {
  form.querySelectorAll(".err").forEach(el => (el.textContent = errors[el.dataset.for] || ""));
}

function validateForm(data) {
  const errors = {};
  for (const [key, check] of Object.entries(rules)) {
    if (editingId && key === "emp_id") continue;
    const r = check((data[key] || "").trim());
    if (r !== true) errors[key] = r;
  }
  showErrors(errors);
  return Object.keys(errors).length === 0;
}

function notify(text, type = "ok") {
  msg.textContent = text;
  msg.className = type;
}

// ---------- API helper ----------
async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || "Request failed");
    err.fields = data.fields;
    throw err;
  }
  return data;
}

// ---------- rendering (no page reload) ----------
function cell(text) {
  const td = document.createElement("td");
  td.textContent = text; // textContent avoids HTML injection
  return td;
}

function render(list) {
  body.replaceChildren();
  document.getElementById("count").textContent = `(${list.length})`;
  if (!list.length) {
    const tr = document.createElement("tr");
    const td = cell("No employees found");
    td.colSpan = 7;
    td.className = "empty";
    tr.append(td);
    body.append(tr);
    return;
  }
  for (const e of list) {
    const tr = document.createElement("tr");
    tr.append(cell(e.emp_id), cell(e.name), cell(e.department), cell(e.designation),
      cell(Number(e.salary).toLocaleString("en-IN")), cell(e.contact));
    const actions = document.createElement("td");
    actions.className = "actions-cell";
    const edit = document.createElement("button");
    edit.textContent = "Edit"; edit.className = "small";
    edit.onclick = () => startEdit(e);
    const del = document.createElement("button");
    del.textContent = "Delete"; del.className = "small danger";
    del.onclick = () => removeEmployee(e);
    actions.append(edit, del);
    tr.append(actions);
    body.append(tr);
  }
}

async function load() {
  const params = new URLSearchParams({ q: searchInput.value.trim(), field: searchField.value });
  try {
    render(await api(`${API}?${params}`));
  } catch (err) {
    notify(err.message, "error");
  }
}

// ---------- CRUD actions ----------
form.addEventListener("submit", async ev => {
  ev.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  Object.keys(data).forEach(k => (data[k] = data[k].trim()));
  if (!validateForm(data)) return;
  try {
    if (editingId) {
      await api(`${API}/${encodeURIComponent(editingId)}`, { method: "PUT", body: JSON.stringify(data) });
      notify(`Employee ${editingId} updated`);
    } else {
      await api(API, { method: "POST", body: JSON.stringify(data) });
      notify(`Employee ${data.emp_id} added`);
    }
    resetForm();
    load();
  } catch (err) {
    if (err.fields) showErrors(err.fields);
    notify(err.message, "error");
  }
});

function startEdit(e) {
  editingId = e.emp_id;
  for (const key of ["emp_id", "name", "department", "designation", "salary", "contact"]) {
    form.elements[key].value = e[key];
  }
  form.elements.emp_id.readOnly = true;
  formTitle.textContent = `Edit Employee ${e.emp_id}`;
  submitBtn.textContent = "Save Changes";
  cancelBtn.hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetForm() {
  editingId = null;
  form.reset();
  form.elements.emp_id.readOnly = false;
  formTitle.textContent = "Add Employee";
  submitBtn.textContent = "Add Employee";
  cancelBtn.hidden = true;
  showErrors({});
}
cancelBtn.addEventListener("click", () => { resetForm(); notify(""); });

async function removeEmployee(e) {
  if (!confirm(`Delete ${e.name} (${e.emp_id})?`)) return;
  try {
    await api(`${API}/${encodeURIComponent(e.emp_id)}`, { method: "DELETE" });
    notify(`Employee ${e.emp_id} deleted`);
    if (editingId === e.emp_id) resetForm();
  } catch (err) {
    notify(err.message, "error");
  }
  load();
}

// debounced live search
let timer;
searchInput.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(load, 250); });
searchField.addEventListener("change", load);

load();
