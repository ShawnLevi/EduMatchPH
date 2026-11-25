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
  const ys = String(csv).split(",").map(Number).filter(Boolean).sort((a, b) => a - b);
  if (ys.length >= 5) return "All years";
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
  if (res.status === 401) { window.location.href = "login.html"; throw new Error("Please log in first"); }
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
  play: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 4 20 12 6 20 6 4"/></svg>',
  print: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="7"/></svg>',
  compare: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="7" height="16" rx="1.5"/><rect x="14" y="4" width="7" height="16" rx="1.5"/></svg>',
  sliders: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/></svg>',
  users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  trophy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4a2 2 0 0 1-2-2V5h4M18 9h2a2 2 0 0 0 2-2V5h-4M6 4h12v6a6 6 0 0 1-12 0zM12 16v4M8 20h8"/></svg>',
  grid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
  logout: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/></svg>',
  shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  history: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 3"/></svg>',
  key: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="7.5" cy="15.5" r="4.5"/><path d="m21 2-9.6 9.6M15.5 7.5l3 3"/></svg>',
  archive: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="5" rx="1"/><path d="M4 9v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9M10 13h4"/></svg>',
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
    window.location.href = "login.html";
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
async function logout() {
  try {
    await apiFetch("/api/logout", { method: "POST" });
  } catch (err) {
    if (err && err.status !== 401) toast(friendlyError(err), "error");
  }
  try { sessionStorage.setItem("edumatch_logged_out", "1"); } catch (e) {}
  window.location.href = "login.html?logged_out=1";
}
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

function hexToRgb(hex) {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(String(hex || "").trim());
  return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : null;
}

function applyOrgTheme(me) {
  if (!me) return;
  if (String(me.role || "").toLowerCase() === "super_admin") return;
  const org = me.organization || me;
  const root = document.documentElement.style;
  if (org.theme_primary_color) {
    root.setProperty("--navy-900", org.theme_primary_color);
    root.setProperty("--navy-800", org.theme_primary_color);
  }
  if (org.theme_accent_color) {
    root.setProperty("--amber-500", org.theme_accent_color);
    root.setProperty("--amber-600", org.theme_accent_color);
  }
  const surfOp = org.theme_surface_opacity != null ? Number(org.theme_surface_opacity) : 0.94;
  if (org.theme_bg_image) {
    document.body.classList.add("has-bg-image");
    root.setProperty("--org-bg-image", `url("${org.theme_bg_image.replace(/"/g, '\\"')}")`);
    root.setProperty("--org-bg-opacity", String(org.theme_bg_opacity != null ? org.theme_bg_opacity : 1));
    const rgb = hexToRgb(org.theme_bg_color || "#FBF8F2") || [251, 248, 242];
    document.body.classList.add("has-surface");
    root.setProperty("--org-surface-bg", `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${surfOp})`);
  } else if (org.theme_bg_color) {
    const rgb = hexToRgb(org.theme_bg_color);
    if (rgb) {
      document.body.classList.add("has-surface");
      root.setProperty("--org-surface-bg", `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${surfOp})`);
    }
    root.setProperty("--cream", org.theme_bg_color);
  }
  if (org.logo_path) {
    const img = $(".brand img");
    if (img) {
      img.src = org.logo_path;
      img.onerror = () => { img.src = "EduMatchPH_logo.jpg"; };
    }
  }
}

function setHeaderAvatar(me) {
  const el = document.getElementById("avatar");
  if (!el || !me) return;
  if (me.avatar_url) {
    el.innerHTML = `<img src="${escapeHtml(me.avatar_url)}" alt="">`;
    const img = el.querySelector("img");
    if (img) img.onerror = () => {
      el.textContent = String(me.full_name || "A").split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
    };
  } else {
    el.textContent = String(me.full_name || "A").split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
  }
}

function openProfileModal(me) {
  let pendingAvatar = me.avatar_url || null;
  const initials = String(me.full_name || "A").split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
  const layer = openModal(
    `<div class="modal-head"><h2>Profile Management</h2></div>` +
    `<form id="prof-form" novalidate>` +
    `<div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem">` +
    `<div class="avatar" id="prof-preview" style="width:60px;height:60px;font-size:1.15rem;flex:none;background:var(--navy-900);color:#fff">${pendingAvatar ? `<img src="${escapeHtml(pendingAvatar)}" alt="">` : escapeHtml(initials)}</div>` +
    `<div style="flex:1"><label class="label" for="prof-file">Profile photo</label>` +
    `<input type="file" id="prof-file" accept="image/*" style="margin-top:.25rem;font-size:.82rem">` +
    `<div class="toolbar" style="margin-top:.35rem"><button type="button" class="btn-ghost small" id="prof-clear">Remove photo</button><span class="hint">PNG/JPG under 1 MB</span></div></div></div>` +
    `<div class="grid2" style="grid-template-columns:1fr">` +
    `<div class="field"><label for="prof-name">Full name</label><input type="text" id="prof-name" value="${escapeHtml(me.full_name || "")}" required><span class="field-error" data-e="name"></span></div>` +
    `<div class="field"><label>Email</label><input type="text" value="${escapeHtml(me.email || "")}" disabled></div>` +
    `<div class="field"><label>Organization &amp; Role</label><input type="text" value="${escapeHtml(String(me.organization_id || "").toUpperCase())} · ${escapeHtml(me.role || "admin")}" disabled></div>` +
    `</div><div class="modal-actions"><button type="button" class="btn-secondary" data-cancel>Cancel</button><button type="submit" class="btn-primary" id="prof-save">Save profile</button></div></form>`
  );
  const f = $("#prof-form", layer.el);
  const prev = $("#prof-preview", layer.el);
  $("#prof-file", f).addEventListener("change", (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    if (file.size > 1_000_000) { toast("Please choose an image smaller than 1 MB.", "error"); e.target.value = ""; return; }
    const reader = new FileReader();
    reader.onload = () => {
      pendingAvatar = String(reader.result || "");
      prev.innerHTML = `<img src="${escapeHtml(pendingAvatar)}" alt="">`;
    };
    reader.readAsDataURL(file);
  });
  $("#prof-clear", f).addEventListener("click", () => {
    pendingAvatar = null;
    $("#prof-file", f).value = "";
    prev.textContent = initials;
  });
  $("[data-cancel]", f).addEventListener("click", () => layer.close());
  f.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = $("#prof-name", f).value.trim();
    if (!name) { $("[data-e=name]", f).textContent = "Full name is required."; return; }
    await withLoading($("#prof-save", f), async () => {
      try {
        const res = await apiFetch("/api/me/profile", {
          method: "PUT", headers: JSON_HEADERS,
          body: JSON.stringify({ full_name: name, avatar_url: pendingAvatar }),
        });
        me.full_name = res.full_name;
        me.avatar_url = res.avatar_url;
        const nameEl = document.getElementById("admin-name");
        const metaEl = document.getElementById("acct-meta-name");
        if (nameEl) nameEl.textContent = res.full_name;
        if (metaEl) metaEl.textContent = res.full_name;
        setHeaderAvatar(me);
        layer.close();
        toast("Profile updated.", "success");
      } catch (er) { $("[data-e=name]", f).textContent = friendlyError(er); }
    });
  });
}

function openChangePasswordModal({ forced = false } = {}) {
  const layer = openModal(
    `<div class="modal-head"><h2>${forced ? "Password change required" : "Change password"}</h2></div>` +
    (forced ? `<div class="alert warn" style="margin-bottom:.9rem">For your security, please set a new password before continuing.</div>` : "") +
    `<form id="cp-form" novalidate><div class="grid2" style="grid-template-columns:1fr">` +
    `<div class="field"><label for="cp-cur">Current password</label><input type="password" id="cp-cur" autocomplete="current-password" required><span class="field-error" data-e="cur"></span></div>` +
    `<div class="field"><label for="cp-new">New password</label><input type="password" id="cp-new" autocomplete="new-password" required><span class="hint">At least 8 characters.</span><span class="field-error" data-e="new"></span></div>` +
    `<div class="field"><label for="cp-con">Confirm new password</label><input type="password" id="cp-con" autocomplete="new-password" required><span class="field-error" data-e="con"></span></div>` +
    `</div><div class="modal-actions">${forced ? "" : '<button type="button" class="btn-secondary" data-cancel>Cancel</button>'}<button type="submit" class="btn-primary" id="cp-save">Update password</button></div></form>`
  );
  const f = $("#cp-form", layer.el);
  const cancel = $("[data-cancel]", layer.el);
  if (cancel) cancel.addEventListener("click", () => layer.close());
  f.addEventListener("submit", async (e) => {
    e.preventDefault();
    $$("[data-e]", f).forEach((x) => (x.textContent = ""));
    const cur = $("#cp-cur", f).value, nw = $("#cp-new", f).value, con = $("#cp-con", f).value;
    const err = (k, t) => { $(`[data-e=${k}]`, f).textContent = t; return 1; };
    let bad = 0;
    if (!cur) bad += err("cur", "Enter your current password.");
    if (nw.length < 8) bad += err("new", "New password must be at least 8 characters.");
    if (nw !== con) bad += err("con", "Passwords do not match.");
    if (bad) return;
    await withLoading($("#cp-save", f), async () => {
      try {
        await apiFetch("/api/change-password", { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ current_password: cur, new_password: nw }) });
        layer.close();
        toast("Password updated successfully.", "success");
      } catch (er) { err("cur", friendlyError(er)); }
    });
  });
}

async function renderShell(active) {
  const sid = getScholarshipIdFromUrl();
  let nav = `<a href="programs.html" class="${active === "programs" ? "active" : ""}">${ICON.grid}All programs</a>`;
  if (sid) {
    const q = "?scholarship=" + encodeURIComponent(sid);
    const tab = (key, file, label, icon) => `<a href="${file}${q}" class="${active === key ? "active" : ""}">${icon}${label}</a>`;
    nav += tab("applicants", "applicants.html", "Applicants &amp; Screening", ICON.users) +
           tab("ranking", "ranking.html", "Ranking &amp; Shortlist", ICON.trophy) +
           tab("compare", "compare.html", "Compare", ICON.compare) +
           tab("edit", "program-form.html", "Edit program", ICON.sliders);
  }
  nav += `<a href="audit-logs.html" class="${active === "audit" ? "active" : ""}" id="nav-audit" hidden>${ICON.history}Audit logs</a>`;
  nav += `<a href="super-admin.html" class="${active === "super" ? "active" : ""}" id="nav-super" hidden>${ICON.shield}Super Admin</a>`;
  document.getElementById("shell").innerHTML =
    '<header class="app-header"><a class="brand" href="programs.html"><img src="EduMatchPH_logo.jpg" alt="">EduMatch PH</a>' +
    '<div class="who"><span class="org-badge" id="org-name"></span>' +
    '<div class="account-menu" id="account-menu">' +
    '<button class="account-trigger" id="account-trigger" type="button" aria-expanded="false" aria-haspopup="menu">' +
    '<span class="avatar" id="avatar" aria-hidden="true"></span>' +
    '<span class="name" id="admin-name"></span><span class="caret">▾</span></button>' +
    '<div class="account-dropdown" id="account-dropdown" role="menu" hidden>' +
    '<div class="acct-meta"><strong id="acct-meta-name"></strong><span id="acct-meta-role"></span></div>' +
    '<button type="button" id="menu-profile" role="menuitem">' + ICON.users + 'Profile management</button>' +
    '<button type="button" id="menu-chpwd" role="menuitem">' + ICON.key + 'Change password</button>' +
    '<button type="button" id="menu-logout" class="danger" role="menuitem">' + ICON.logout + 'Log out</button>' +
    '</div></div></div></header>' +
    '<div class="crumbs" id="crumbs"></div><nav class="subnav" aria-label="Sections">' + nav + "</nav>";

  let CURRENT_ME = null;
  const trigger = document.getElementById("account-trigger");
  const dropdown = document.getElementById("account-dropdown");
  const closeMenu = () => { dropdown.hidden = true; trigger.setAttribute("aria-expanded", "false"); };
  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const open = dropdown.hidden;
    dropdown.hidden = !open;
    trigger.setAttribute("aria-expanded", open ? "true" : "false");
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#account-menu")) closeMenu();
  });
  document.getElementById("menu-profile").addEventListener("click", () => {
    closeMenu();
    if (CURRENT_ME) openProfileModal(CURRENT_ME);
  });
  document.getElementById("menu-chpwd").addEventListener("click", () => {
    closeMenu();
    openChangePasswordModal();
  });
  document.getElementById("menu-logout").addEventListener("click", async () => {
    closeMenu();
    const ok = await confirmDialog({
      title: "Log out?",
      message: "Are you sure you want to log out of EduMatch PH?",
      confirmText: "Log out",
      cancelText: "Cancel",
    });
    if (ok) await logout();
  });
  const crumbs = (last) => `<a href="programs.html">Programs</a>` + (last ? `<span class="sep">›</span>${last}` : "");
  document.getElementById("crumbs").innerHTML = crumbs(sid ? '<span class="skeleton" style="display:inline-block;width:140px;height:12px;vertical-align:middle"></span>' :
    active === "new" ? "New program" : active === "audit" ? "Audit logs" : active === "super" ? "Super Admin" : "");
  getMe().then((me) => {
    CURRENT_ME = me;
    document.getElementById("admin-name").textContent = me.full_name;
    document.getElementById("acct-meta-name").textContent = me.full_name;
    document.getElementById("acct-meta-role").textContent = `${String(me.organization_id || "").toUpperCase()} · ${me.role || "admin"}`;
    setHeaderAvatar(me);
    document.getElementById("org-name").textContent = String(me.role || "").toLowerCase() === "super_admin" ? "GLOBAL" : String(me.organization_id).toUpperCase();
    document.body.dataset.org = String(me.organization_id).toLowerCase();
    applyOrgTheme(me);
    const role = String(me.role || "").toLowerCase();
    const isSuper = Boolean(me.is_super_admin || role === "super_admin" || role === "superadmin");
    if (isSuper || role === "owner") {
      const aLink = document.getElementById("nav-audit");
      if (aLink) aLink.hidden = false;
      const sLink = document.getElementById("nav-super");
      if (sLink) {
        sLink.hidden = false;
        if (!isSuper) sLink.innerHTML = ICON.shield + "Team &amp; Branding";
      }
    }
    if (me.must_change_pw || me.must_change_password || me.force_password_change) {
      openChangePasswordModal({ forced: true });
    }
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
