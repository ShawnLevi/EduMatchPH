// EduMatch PH administrator system: shared helpers used by every page.
// Backend and page must both use "localhost" (not 127.0.0.1) so the login cookie is sent.
const API = "http://localhost:5000";
const STATUS_LABELS = { SHORTLIST: "Shortlisted", WAITLIST: "Waitlisted" };
const JSON_HEADERS = { "Content-Type": "application/json" };

// ---------- small utilities ----------
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
function getScholarshipIdFromUrl() { return new URLSearchParams(window.location.search).get("scholarship"); }
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}
function debounce(fn, ms = 180) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function peso(n) { return "₱" + Number(n).toLocaleString("en-PH", { maximumFractionDigits: 0 }); }
function pesoShort(n) {
  n = Number(n);
  if (n >= 1e6) return "₱" + (n / 1e6).toFixed(n % 1e6 ? 1 : 0) + "M";
  if (n >= 1e3) return "₱" + Math.round(n / 1e3) + "K";
  return "₱" + n;
}
function yearsLabel(csv) {
  const ys = String(csv).split(",").map(Number).sort();
  if (ys.length === 4) return "All years";
  const contiguous = ys.every((y, i) => i === 0 || y === ys[i - 1] + 1);
  return ys.length > 1 && contiguous ? `Year ${ys[0]}–${ys[ys.length - 1]}` : "Year " + ys.join(", ");
}
function store(key, value) { try { if (value === undefined) return localStorage.getItem(key); localStorage.setItem(key, value); } catch (e) { return null; } }
function animateNumber(el, to, ms = 600) {
  if (!el) return;
  to = Number(to);
  if (!isFinite(to) || window.matchMedia("(prefers-reduced-motion: reduce)").matches) { el.textContent = to; return; }
  const start = performance.now();
  const step = (now) => {
    const p = Math.min(1, (now - start) / ms), eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(to * eased);
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
function skeletonRows(cols, rows = 5) {
  return Array.from({ length: rows }, () =>
    "<tr>" + Array.from({ length: cols }, () => '<td><span class="skeleton" style="height:14px"></span></td>').join("") + "</tr>").join("");
}
function downloadBlob(blob, filename) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob); link.download = filename;
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}
// Download a file from the server (for example a CSV export). Shows the server's message when it refuses.
async function downloadFile(path, filename) {
  const res = await fetch(API + path, { credentials: "include" });
  if (res.status === 401) { window.location.href = "index.html"; throw new Error("Please log in first"); }
  if (!res.ok) {
    let msg = null; try { msg = (await res.json()).error; } catch (e) { /* no JSON body */ }
    throw new Error(msg || `The file could not be downloaded (error ${res.status}). Please try again.`);
  }
  downloadBlob(await res.blob(), filename);
}
// Turn rows (arrays of text) into CSV text. Cells that a spreadsheet could run as a formula are neutralized.
function csvCell(v) {
  let s = v == null ? "" : String(v);
  if (/^[=+@]/.test(s) || /^-(?!\d)/.test(s)) s = "'" + s;
  return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}
function toCsv(rows) { return "\ufeff" + rows.map((r) => r.map(csvCell).join(",")).join("\r\n") + "\r\n"; }
const ICON = {
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  upload: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4m0 0L7 9m5-5 5 5M4 20h16"/></svg>',
  edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h4L19 9a2.1 2.1 0 0 0-3-3L5 17z"/><path d="m14 7 3 3"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
  inbox: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13l3-8h12l3 8v6H3z"/><path d="M3 13h5l1 3h6l1-3h5"/></svg>',
  download: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v12m0 0 5-5m-5 5-5-5M4 20h16"/></svg>',
};

// ---------- toasts ----------
function toast(message, type = "info", opts = {}) {
  let box = $(".toasts");
  if (!box) { box = document.createElement("div"); box.className = "toasts"; box.setAttribute("aria-live", "polite"); box.setAttribute("role", "status"); document.body.appendChild(box); }
  const el = document.createElement("div");
  el.className = "toast " + type;
  el.innerHTML = `<span>${escapeHtml(message)}</span>`;
  const remove = () => { el.classList.add("out"); setTimeout(() => el.remove(), 260); };
  if (opts.action) {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = opts.action.label;
    b.addEventListener("click", () => { opts.action.onClick(); remove(); });
    el.appendChild(b);
  }
  box.appendChild(el);
  setTimeout(remove, opts.duration || (type === "error" ? 7000 : 4200));
  return el;
}

// ---------- modal, confirm dialog, drawer ----------
const _layers = [];
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && _layers.length) _layers[_layers.length - 1].close(); });
function openModal(html, { wide = false, onClose } = {}) {
  const overlay = document.createElement("div");
  overlay.className = "overlay";
  overlay.innerHTML = `<div class="modal${wide ? " wide" : ""}" role="dialog" aria-modal="true">${html}</div>`;
  const prevFocus = document.activeElement;
  const layer = { el: overlay.firstElementChild, close() {
    const i = _layers.indexOf(layer); if (i >= 0) _layers.splice(i, 1);
    overlay.remove(); if (prevFocus && prevFocus.focus) prevFocus.focus(); if (onClose) onClose();
  } };
  overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) layer.close(); });
  document.body.appendChild(overlay); _layers.push(layer);
  const first = $("input:not([type=hidden]),select,textarea", layer.el) || $("button", layer.el);
  if (first) setTimeout(() => first.focus(), 30);
  return layer;
}
function confirmDialog({ title, message, confirmText = "Confirm", cancelText = "Cancel", danger = false }) {
  return new Promise((resolve) => {
    let settled = false;
    const done = (v) => { if (!settled) { settled = true; resolve(v); } };
    const layer = openModal(
      `<div class="modal-head"><h2>${escapeHtml(title)}</h2></div><p style="margin:0;color:var(--ink-muted)">${escapeHtml(message)}</p>` +
      `<div class="modal-actions"><button class="btn-secondary" data-no type="button">${escapeHtml(cancelText)}</button>` +
      `<button class="${danger ? "btn-danger" : "btn-primary"}" data-yes type="button">${escapeHtml(confirmText)}</button></div>`,
      { onClose: () => done(false) });
    $("[data-no]", layer.el).addEventListener("click", () => layer.close());
    $("[data-yes]", layer.el).addEventListener("click", () => { done(true); layer.close(); });
    $("[data-yes]", layer.el).focus();
  });
}
function openDrawer({ title, subtitle = "", body = "", footer = "", onClose } = {}) {
  const wrap = document.createElement("div");
  wrap.innerHTML = `<div class="drawer-overlay"></div><aside class="drawer" role="dialog" aria-modal="true">` +
    `<div class="drawer-head"><div><h2 data-title></h2><div class="hint" data-sub></div></div>` +
    `<button class="icon-btn" data-x type="button" aria-label="Close" style="font-size:1.3rem;line-height:1">×</button></div>` +
    `<div class="drawer-body" data-body></div><div class="drawer-foot" data-foot hidden></div></aside>`;
  const prevFocus = document.activeElement;
  const layer = { el: wrap, close() {
    const i = _layers.indexOf(layer); if (i >= 0) _layers.splice(i, 1);
    wrap.remove(); if (prevFocus && prevFocus.focus) prevFocus.focus(); if (onClose) onClose();
  }, set({ title, subtitle, body, footer }) {
    if (title != null) $("[data-title]", wrap).textContent = title;
    if (subtitle != null) $("[data-sub]", wrap).innerHTML = subtitle;
    if (body != null) $("[data-body]", wrap).innerHTML = body;
    if (footer != null) { const f = $("[data-foot]", wrap); f.innerHTML = footer; f.hidden = !footer; }
  } };
  layer.set({ title, subtitle, body, footer });
  $(".drawer-overlay", wrap).addEventListener("click", () => layer.close());
  $("[data-x]", wrap).addEventListener("click", () => layer.close());
  document.body.appendChild(wrap); _layers.push(layer);
  return layer;
}

// ---------- server calls ----------
function friendlyError(err) {
  if (err instanceof TypeError) return "EduMatch PH cannot connect to its server right now. Check your connection and try again. If the problem continues, contact your system administrator.";
  return err && err.message ? err.message : "The request could not be completed. Please try again.";
}
function showBackendError(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.innerHTML = '<span class="backend-error">' + escapeHtml(friendlyError(new TypeError())) + "</span>";
}
// Every call to the server goes through this. credentials: "include" sends the login cookie.
async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, { credentials: "include", ...options });
  let data = null;
  try { data = await res.json(); } catch (e) { /* no JSON body */ }
  if (res.status === 401 && !path.startsWith("/api/login")) {
    window.location.href = "index.html";
    throw new Error("Please log in first");
  }
  if (!res.ok) { const err = new Error((data && data.error) || `The request could not be completed (error ${res.status}). Please try again.`); err.status = res.status; throw err; }
  return data;
}
function showError(elementId, err) {
  const el = document.getElementById(elementId);
  if (el) el.innerHTML = '<span class="backend-error">' + escapeHtml(friendlyError(err)) + "</span>";
}
function showMessage(elementId, text) { const el = document.getElementById(elementId); if (el) el.textContent = text; }
// Runs an async action with a spinner on the button, so the user sees something is happening.
async function withLoading(btn, fn) {
  if (!btn) return fn();
  btn.classList.add("loading"); btn.disabled = true;
  try { return await fn(); } finally { btn.classList.remove("loading"); btn.disabled = false; }
}

function login(organizationId, email, password) {
  return apiFetch("/api/login", { method: "POST", headers: JSON_HEADERS,
    body: JSON.stringify({ organization_id: organizationId, email, password }) });
}
function logout() { return apiFetch("/api/logout", { method: "POST" }).then(() => { window.location.href = "index.html"; }); }
function getMe() { return apiFetch("/api/me"); }

// ---------- dropdowns ----------
function fillSelect(id, values) {
  document.getElementById(id).innerHTML = '<option value="">Choose...</option>' +
    values.map((v) => `<option>${escapeHtml(v)}</option>`).join("");
}
let GRADE_SCALES = {};
function scaleHintText(scale) {
  if (!scale) return "";
  return `${scale.label}: from ${scale.min_value} to ${scale.max_value}. ` +
    (scale.higher_is_better ? "A higher number is better." : "A lower number is better.");
}
let META = null;
async function loadMeta() {
  if (META) return META;
  META = await apiFetch("/api/meta");
  GRADE_SCALES = Object.fromEntries(META.grade_scales.map((s) => [s.scale_id, s]));
  return META;
}

// ---------- page shell: header, breadcrumb, sub navigation, program header + stepper ----------
// active: "programs" | "applicants" | "ranking" | "compare" | "edit" | "new"
let PROGRAM = null;
function statusPill(status) {
  const cls = status === "Closed" ? "no" : status === "Open" ? "ok" : "neutral";
  return `<span class="pill ${cls}">${escapeHtml(status)}</span>`;
}
function programTitle(p) { return `${p.scholarship_name} (${p.provider || ""})`; }
function ruleSummaryChips(p) {
  const gwa = p.higher_is_better ? `GWA ≥ ${p.gwa_limit}` : `GWA ≤ ${p.gwa_limit}`;
  return [gwa, "Income ≤ " + pesoShort(p.income_cap), "Entrance ≥ " + p.min_entrance,
          p.eligible_field === "ANY" ? "Any course" : p.eligible_field, yearsLabel(p.eligible_years), p.location_req]
    .map((t) => `<span class="rule-chip">${escapeHtml(t)}</span>`).join("");
}
function stepperHtml(program, sid, active) {
  const order = { Open: 0, Screening: 1, Ranking: 2, Closed: 3 };
  const lvl = order[program.status] ?? 0;
  const steps = [
    ["Add applicants", "applicants.html", lvl >= 1 ? "done" : "current"],
    ["Run screening", "applicants.html", lvl >= 2 ? "done" : lvl === 1 ? "done" : ""],
    ["Run ranking", "ranking.html", lvl >= 3 || lvl === 2 ? "done" : lvl === 1 ? "current" : ""],
    ["Review shortlist", "ranking.html", lvl === 3 ? "done" : lvl === 2 ? "current" : ""],
  ];
  if (lvl === 0) { steps[0][2] = "current"; }
  return `<ol class="stepper" aria-label="Progress">` + steps.map(([label, file, state], i) =>
    `<li class="${state}"><a href="${file}?scholarship=${encodeURIComponent(sid)}"><span class="num">${state === "done" ? "✓" : i + 1}</span>` +
    `<span class="lbl">${label}<span class="sub" id="step-sub-${i}"></span></span></a></li>`).join("") + `</ol>`;
}
function setStepSub(i, text) { const el = document.getElementById("step-sub-" + i); if (el) el.textContent = text; }

async function renderShell(active) {
  const sid = getScholarshipIdFromUrl();
  let nav = '<a href="programs.html" class="' + (active === "programs" ? "active" : "") + '">All programs</a>';
  if (sid) {
    const q = "?scholarship=" + encodeURIComponent(sid);
    const tab = (key, file, label) => `<a href="${file}${q}" class="${active === key ? "active" : ""}">${label}</a>`;
    nav += tab("applicants", "applicants.html", "Applicants &amp; Screening") + tab("ranking", "ranking.html", "Ranking &amp; Shortlist") +
           tab("compare", "compare.html", "Compare") + tab("edit", "program-form.html", "Edit program");
  }
  document.getElementById("shell").innerHTML =
    '<header class="app-header"><a class="brand" href="programs.html"><img src="EduMatchPH_logo.jpg" alt="">EduMatch PH</a>' +
    '<div class="who"><span class="org-badge" id="org-name"></span><span class="avatar" id="avatar" aria-hidden="true"></span>' +
    '<span class="name" id="admin-name"></span><button class="btn-secondary small" id="logout-btn" type="button">Log out</button></div></header>' +
    '<div class="crumbs" id="crumbs"></div><nav class="subnav" aria-label="Sections">' + nav + "</nav>";
  document.getElementById("logout-btn").addEventListener("click", logout);
  const crumbs = (last) => `<a href="programs.html">Programs</a>` + (last ? `<span class="sep">›</span>${last}` : "");
  document.getElementById("crumbs").innerHTML = crumbs(sid ? '<span class="skeleton" style="display:inline-block;width:140px;height:12px;vertical-align:middle"></span>' :
    active === "new" ? "New program" : "");
  getMe().then((me) => {
    document.getElementById("admin-name").textContent = me.full_name;
    document.getElementById("avatar").textContent = me.full_name.split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
    document.getElementById("org-name").textContent = String(me.organization_id).toUpperCase();
  }).catch(() => {});
  if (!sid) return null;
  try {
    PROGRAM = await apiFetch(`/api/scholarships/${sid}`);
    document.getElementById("crumbs").innerHTML = crumbs(escapeHtml(PROGRAM.scholarship_name));
    const head = document.getElementById("prog-head");
    if (head) {
      head.innerHTML = `<div class="prog-head"><div><h1>${escapeHtml(PROGRAM.scholarship_name)}</h1>` +
        `<div class="prog-meta">${escapeHtml(PROGRAM.provider || "")}<span class="dot">•</span>${statusPill(PROGRAM.status)}` +
        `<span class="dot">•</span>${PROGRAM.available_slots} slots${PROGRAM.application_deadline ? `<span class="dot">•</span>Deadline ${escapeHtml(PROGRAM.application_deadline)}` : ""}</div>` +
        `<div class="chips" style="margin-top:.6rem">${ruleSummaryChips(PROGRAM)}</div></div></div>` +
        stepperHtml(PROGRAM, sid, active);
    }
    document.title = `${PROGRAM.scholarship_name} — EduMatch PH`;
  } catch (err) {
    document.getElementById("crumbs").innerHTML = crumbs("");
    if (err.status === 404) { toast("That program was not found.", "error"); setTimeout(() => (window.location.href = "programs.html"), 1200); }
  }
  return PROGRAM;
}
async function refreshProgram() {
  const sid = getScholarshipIdFromUrl();
  if (!sid) return null;
  PROGRAM = await apiFetch(`/api/scholarships/${sid}`);
  const head = document.getElementById("prog-head");
  if (head) {
    const meta = $(".prog-meta", head);
    if (meta) meta.innerHTML = `${escapeHtml(PROGRAM.provider || "")}<span class="dot">•</span>${statusPill(PROGRAM.status)}<span class="dot">•</span>${PROGRAM.available_slots} slots` +
      (PROGRAM.application_deadline ? `<span class="dot">•</span>Deadline ${escapeHtml(PROGRAM.application_deadline)}` : "");
    const st = $(".stepper", head); if (st) st.outerHTML = stepperHtml(PROGRAM, sid);
  }
  return PROGRAM;
}
// Press "/" anywhere to jump to the page's search box.
document.addEventListener("keydown", (e) => {
  if (e.key !== "/" || e.ctrlKey || e.metaKey) return;
  const t = e.target; if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
  const s = $("[data-search]"); if (s) { e.preventDefault(); s.focus(); }
});
