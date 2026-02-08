/* ================================================================
   Work Schedule – frontend application (plain JS, no framework)
   ================================================================ */

const API = window.location.origin;

// ── State ───────────────────────────────────────────────────────
let quarterOffset = 0;          // 0 = current quarter
let tlQuarterOffset = 0;        // timeline quarter offset
let shiftsCache   = {};         // date → shift obj
let currentView   = "calendar";
let activeTool    = null;       // null | "day8" | "day12" | "night12" | "eraser"

// ── Boot ────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initToolbar();
  renderCalendar();
  initModal();
  initSSE();
});

// ── Server-Sent Events (live sync across devices) ───────────────
let _sseDebounce = null;

function initSSE() {
  const es = new EventSource(`${API}/api/events`);

  es.onmessage = (ev) => {
    // Debounce rapid-fire events (e.g. bulk changes) to one refresh
    clearTimeout(_sseDebounce);
    _sseDebounce = setTimeout(() => refreshCurrentView(), 300);
  };

  es.onerror = () => {
    // Browser auto-reconnects; we just log it
    console.warn("SSE connection lost – reconnecting…");
  };
}

// ── Paint Toolbar ───────────────────────────────────────────────
function initToolbar() {
  document.querySelectorAll(".paint-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tool = btn.dataset.tool || null;
      activeTool = (activeTool === tool) ? null : tool;   // toggle
      updateToolbarUI();
    });
  });
  updateToolbarUI();
}

function updateToolbarUI() {
  document.querySelectorAll(".paint-btn").forEach(btn => {
    const tool = btn.dataset.tool || null;
    btn.classList.toggle("active", tool === activeTool && tool !== null);
  });
  // Show cursor hint on body
  document.body.classList.toggle("paint-mode", activeTool !== null);
}

async function paintCell(date, existingShift) {
  if (!activeTool) { openModal(date, existingShift); return; }
  if (activeTool === "eraser") {
    if (existingShift) {
      await fetchJSON(`/api/shifts/${date}`, { method: "DELETE" });
      refreshCurrentView();
    }
    return;
  }
  // Set shift
  await fetchJSON(`/api/shifts/${date}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type: activeTool }),
  });
  refreshCurrentView();
}

// ── Tabs ────────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
      btn.classList.add("active");
      const view = btn.dataset.view;
      document.getElementById(`view-${view}`).classList.add("active");
      currentView = view;
      if (view === "calendar")  renderCalendar();
      if (view === "timeline")  renderTimeline();
      if (view === "history")   renderHistory();
    });
  });
}

// ================================================================
//  CALENDAR VIEW
// ================================================================

function getQuarterRange(offset) {
  const now = new Date();
  const qMonth = Math.floor(now.getMonth() / 3) * 3;   // 0,3,6,9
  const startMonth = qMonth + offset * 3;

  const start = new Date(now.getFullYear(), startMonth, 1);
  const end   = new Date(now.getFullYear(), startMonth + 3, 0);   // last day of 3rd month

  return { start, end };
}

async function renderCalendar() {
  const { start, end } = getQuarterRange(quarterOffset);

  // Label
  const qNum = Math.floor(start.getMonth() / 3) + 1;
  document.getElementById("quarter-label").textContent =
    `Q${qNum} ${start.getFullYear()}`;

  // Fetch shifts
  const from = isoDate(start);
  const to   = isoDate(end);
  const shifts = await fetchShifts(from, to);
  shiftsCache = {};
  if (Array.isArray(shifts)) {
    shifts.forEach(s => shiftsCache[s.date] = s);
  }

  // Build 3 months
  const grid = document.getElementById("calendar-grid");
  grid.innerHTML = "";
  for (let m = 0; m < 3; m++) {
    const monthDate = new Date(start.getFullYear(), start.getMonth() + m, 1);
    grid.appendChild(buildMonth(monthDate));
  }

  // Nav
  document.getElementById("prev-quarter").onclick = () => { quarterOffset--; renderCalendar(); };
  document.getElementById("next-quarter").onclick = () => { quarterOffset++; renderCalendar(); };
}

function buildMonth(date) {
  const year = date.getFullYear();
  const month = date.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDow = (new Date(year, month, 1).getDay() + 6) % 7; // Mon=0
  const today = isoDate(new Date());

  const DAYS = ["Pn","Wt","Śr","Cz","Pt","So","Nd"];
  const MONTHS = ["Styczeń","Luty","Marzec","Kwiecień","Maj","Czerwiec",
                  "Lipiec","Sierpień","Wrzesień","Październik","Listopad","Grudzień"];

  const block = el("div", "month-block");
  block.appendChild(el("h4", "", MONTHS[month] + " " + year));

  // Day-of-week header
  const hdr = el("div", "month-header");
  DAYS.forEach(d => { const s = el("span", "", d); hdr.appendChild(s); });
  block.appendChild(hdr);

  // Day cells
  const days = el("div", "month-days");

  // Empty leading cells
  for (let i = 0; i < firstDow; i++) days.appendChild(el("div", "day-cell empty"));

  for (let d = 1; d <= daysInMonth; d++) {
    const iso = `${year}-${pad(month + 1)}-${pad(d)}`;
    const cell = el("div", "day-cell", String(d));

    if (iso === today) cell.classList.add("today");

    const shift = shiftsCache[iso];
    if (shift) cell.classList.add(`shift-${shift.type}`);

    cell.addEventListener("click", () => paintCell(iso, shift));
    days.appendChild(cell);
  }

  block.appendChild(days);
  return block;
}

// ================================================================
//  TIMELINE VIEW
// ================================================================

async function renderTimeline() {
  const { start, end } = getQuarterRange(tlQuarterOffset);
  const now = new Date();
  const today = isoDate(now);

  const MONTHS = ["Styczeń","Luty","Marzec","Kwiecień","Maj","Czerwiec",
                  "Lipiec","Sierpień","Wrzesień","Październik","Listopad","Grudzień"];
  const DOW = ["Nd","Pn","Wt","Śr","Cz","Pt","So"];

  // Quarter label
  const qNum = Math.floor(start.getMonth() / 3) + 1;
  document.getElementById("tl-label").textContent =
    `Q${qNum} ${start.getFullYear()}`;

  // Fetch all shifts for the quarter
  const shifts = await fetchShifts(isoDate(start), isoDate(end));
  const map = {};
  if (Array.isArray(shifts)) {
    shifts.forEach(s => map[s.date] = s);
  }

  const container = document.getElementById("timeline");
  container.innerHTML = "";

  // Build 3 month rows
  for (let m = 0; m < 3; m++) {
    const monthStart = new Date(start.getFullYear(), start.getMonth() + m, 1);
    const monthEnd = new Date(start.getFullYear(), start.getMonth() + m + 1, 0);

    const row = el("div", "tl-month-row");

    // Month label
    const label = el("div", "tl-month-label", MONTHS[monthStart.getMonth()]);
    row.appendChild(label);

    // Scrollable strip of days
    const scrollWrap = el("div", "tl-strip-scroll");
    const strip = el("div", "tl-strip");

    for (let d = new Date(monthStart); d <= monthEnd; d.setDate(d.getDate() + 1)) {
      const iso = isoDate(d);
      const shift = map[iso];
      const isWeekend = d.getDay() === 0 || d.getDay() === 6;

      const col = el("div", "tl-col");
      if (iso === today) col.classList.add("tl-today");
      if (isWeekend) col.classList.add("tl-weekend");

      // Bar
      const bar = el("div", "tl-bar");
      if (shift) {
        bar.classList.add(`shift-${shift.type}`);
        bar.title = `${iso}\n${shift.type} ${shift.start}–${shift.end}`;
      } else {
        bar.classList.add("empty");
        bar.title = iso;
      }
      col.appendChild(bar);

      // Day number
      col.appendChild(el("div", "tl-day", String(d.getDate())));

      // Day-of-week
      const dow = el("div", "tl-dow", DOW[d.getDay()]);
      col.appendChild(dow);

      col.addEventListener("click", () => paintCell(iso, shift));
      strip.appendChild(col);
    }

    scrollWrap.appendChild(strip);
    row.appendChild(scrollWrap);
    container.appendChild(row);

    // Auto-scroll to today within this strip
    const todayEl = strip.querySelector(".tl-today");
    if (todayEl) {
      requestAnimationFrame(() => {
        todayEl.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
      });
    }
  }

  document.getElementById("tl-prev").onclick = () => { tlQuarterOffset--; renderTimeline(); };
  document.getElementById("tl-next").onclick = () => { tlQuarterOffset++; renderTimeline(); };
}

// ================================================================
//  HISTORY VIEW
// ================================================================

async function renderHistory() {
  const tbody = document.querySelector("#history-table tbody");
  tbody.innerHTML = "<tr><td colspan='3'>Ładowanie…</td></tr>";

  const data = await fetchJSON("/api/history?limit=100");
  tbody.innerHTML = "";
  if (!data.length) {
    tbody.innerHTML = "<tr><td colspan='3'>Brak historii</td></tr>";
    return;
  }
  data.forEach(h => {
    const tr = el("tr");
    tr.appendChild(el("td", "", formatTimestamp(h.timestamp)));
    tr.appendChild(el("td", "", h.date));
    tr.appendChild(el("td", "", h.change || "—"));
    tbody.appendChild(tr);
  });

  document.getElementById("undo-btn").onclick = async () => {
    if (!confirm("Cofnąć ostatnią zmianę?")) return;
    await fetchJSON("/api/undo", { method: "POST" });
    refreshCurrentView();
  };
}

// ================================================================
//  MODAL (edit shift)
// ================================================================

function initModal() {
  document.getElementById("modal-cancel").onclick  = closeModal;
  document.getElementById("modal-overlay").onclick  = (e) => {
    if (e.target.id === "modal-overlay") closeModal();
  };
}

let modalDate = null;

function openModal(date, shift) {
  modalDate = date;
  document.getElementById("modal-title").textContent = `Zmiana: ${date}`;
  document.getElementById("modal-type").value = shift ? shift.type : "";
  document.getElementById("modal-overlay").classList.remove("hidden");

  document.getElementById("modal-save").onclick = async () => {
    const type = document.getElementById("modal-type").value;
    if (!type) { alert("Wybierz typ zmiany"); return; }
    await fetchJSON(`/api/shifts/${modalDate}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type }),
    });
    closeModal();
    refreshCurrentView();
  };

  document.getElementById("modal-delete").onclick = async () => {
    if (!confirm(`Usunąć zmianę ${date}?`)) return;
    await fetchJSON(`/api/shifts/${modalDate}`, { method: "DELETE" });
    closeModal();
    refreshCurrentView();
  };
}

function closeModal() {
  document.getElementById("modal-overlay").classList.add("hidden");
  modalDate = null;
}

// ================================================================
//  REFRESH
// ================================================================

function refreshCurrentView() {
  if (currentView === "calendar")  renderCalendar();
  if (currentView === "timeline")  renderTimeline();
  if (currentView === "history")   renderHistory();
}

// ================================================================
//  HELPERS
// ================================================================

async function fetchShifts(from, to) {
  return fetchJSON(`/api/shifts?from=${from}&to=${to}`);
}

async function fetchJSON(path, opts = {}) {
  try {
    const res = await fetch(`${API}${path}`, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      console.error("API error", res.status, err);
      return err;
    }
    return res.json();
  } catch (e) {
    console.error("Fetch failed", e);
    return {};
  }
}

function isoDate(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function pad(n) { return String(n).padStart(2, "0"); }

function formatShortDate(d) {
  const DAYS = ["Nd","Pn","Wt","Śr","Cz","Pt","So"];
  return `${DAYS[d.getDay()]} ${pad(d.getDate())}.${pad(d.getMonth()+1)}`;
}

function formatTimestamp(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  return `${pad(d.getDate())}.${pad(d.getMonth()+1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

// Keyboard shortcut: Ctrl+Z → undo
document.addEventListener("keydown", async (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "z") {
    e.preventDefault();
    const result = await fetchJSON("/api/undo", { method: "POST" });
    if (result.message) {
      console.log("Undo:", result.message);
      refreshCurrentView();
    }
  }
});
