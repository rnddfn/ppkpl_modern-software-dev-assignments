async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
const notesState = { page: 1, pageSize: 5, total: 0 };
const actionsState = { page: 1, pageSize: 5, total: 0 };

function totalPages(state) {
  return Math.max(1, Math.ceil(state.total / state.pageSize));
}

function buildPaginatedUrl(basePath, state) {
  const params = new URLSearchParams({
    page: String(state.page),
    page_size: String(state.pageSize),
  });
  return `${basePath}?${params.toString()}`;
}

function updatePaginationControls(prefix, state) {
  const prevBtn = document.getElementById(`${prefix}-prev`);
  const nextBtn = document.getElementById(`${prefix}-next`);
  const info = document.getElementById(`${prefix}-page-info`);
  const pages = totalPages(state);

  prevBtn.disabled = state.page <= 1;
  nextBtn.disabled = state.page >= pages;
  info.textContent = `Page ${state.page} / ${pages} (${state.total} total)`;
}

async function loadNotes() {
  const list = document.getElementById('notes');
  list.innerHTML = '';
  const data = await fetchJSON(buildPaginatedUrl('/notes/', notesState));
  notesState.total = data.total;
  for (const n of data.items) {
    const li = document.createElement('li');
    li.textContent = `${n.title}: ${n.content}`;
    list.appendChild(li);
  }
  updatePaginationControls('notes', notesState);
}

async function loadActions() {
  const list = document.getElementById('actions');
  list.innerHTML = '';
  const data = await fetchJSON(buildPaginatedUrl('/action-items/', actionsState));
  actionsState.total = data.total;
  for (const a of data.items) {
    const li = document.createElement('li');
    li.textContent = `${a.description} [${a.completed ? 'done' : 'open'}]`;
    if (!a.completed) {
      const btn = document.createElement('button');
      btn.textContent = 'Complete';
      btn.onclick = async () => {
        await fetchJSON(`/action-items/${a.id}/complete`, { method: 'PUT' });
        loadActions();
      };
      li.appendChild(btn);
    }
    list.appendChild(li);
  }
  updatePaginationControls('actions', actionsState);
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('notes-prev').addEventListener('click', () => {
    if (notesState.page <= 1) return;
    notesState.page -= 1;
    loadNotes();
  });

  document.getElementById('notes-next').addEventListener('click', () => {
    if (notesState.page >= totalPages(notesState)) return;
    notesState.page += 1;
    loadNotes();
  });

  document.getElementById('actions-prev').addEventListener('click', () => {
    if (actionsState.page <= 1) return;
    actionsState.page -= 1;
    loadActions();
  });

  document.getElementById('actions-next').addEventListener('click', () => {
    if (actionsState.page >= totalPages(actionsState)) return;
    actionsState.page += 1;
    loadActions();
  });
  document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;
    await fetchJSON('/notes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    });
    e.target.reset();
    notesState.total += 1;
    notesState.page = totalPages(notesState);
    loadNotes();
  });

  document.getElementById('action-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const description = document.getElementById('action-desc').value;
    await fetchJSON('/action-items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    e.target.reset();
    actionsState.total += 1;
    actionsState.page = totalPages(actionsState);
    loadActions();
  });

  loadNotes();
  loadActions();
});
