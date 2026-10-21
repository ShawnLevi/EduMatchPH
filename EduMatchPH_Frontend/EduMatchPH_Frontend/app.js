// EduMatch PH administrator system: shared helpers used by every page.
// Backend and page must both use "localhost" (not 127.0.0.1) so the login cookie is sent.
const API = "http://localhost:5000";
const STATUS_LABELS = { SHORTLIST: "Shortlisted", WAITLIST: "Waitlisted" };
const JSON_HEADERS = { "Content-Type": "application/json" };

function getScholarshipIdFromUrl() {
  return new URLSearchParams(window.location.search).get("scholarship");
}
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}
function showBackendError(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.innerHTML = '<span class="backend-error">Backend not connected. Start the ' +
    "Flask server (python app.py) and refresh this page.</span>";
}

// Every call to the backend goes through this. credentials: "include" sends the login cookie.
async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, { credentials: "include", ...options });
  let data = null;
  try { data = await res.json(); } catch (e) { /* no JSON body */ }
  if (res.status === 401 && !path.startsWith("/api/login")) {
    window.location.href = "index.html";
    throw new Error("Please log in first");
  }
  if (!res.ok) throw new Error((data && data.error) || "HTTP " + res.status);
  return data;
}
function showError(elementId, err) {
  if (err instanceof TypeError) { showBackendError(elementId); return; }
  const el = document.getElementById(elementId);
  if (el) el.innerHTML = '<span class="backend-error">' + escapeHtml(err.message) + "</span>";
}
function showMessage(elementId, text) {
  const el = document.getElementById(elementId);
  if (el) el.textContent = text;
}

function login(organizationId, email, password) {
  return apiFetch("/api/login", { method: "POST", headers: JSON_HEADERS,
    body: JSON.stringify({ organization_id: organizationId, email, password }) });
}
function logout() {
  return apiFetch("/api/logout", { method: "POST" }).then(() => { window.location.href = "index.html"; });
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

// ---------- page shell: header + sub navigation ----------
// active: "programs" | "applicants" | "ranking" | "compare" | "edit" | "new"
async function renderShell(active) {
  const sid = getScholarshipIdFromUrl();
  let nav = '<a href="programs.html" class="' + (active === "programs" ? "active" : "") + '">All programs</a>';
  if (sid) {
    const q = "?scholarship=" + encodeURIComponent(sid);
    const tab = (key, file, label) =>
      `<a href="${file}${q}" class="${active === key ? "active" : ""}">${label}</a>`;
    nav += tab("applicants", "applicants.html", "Applicants &amp; Screening") +
           tab("ranking", "ranking.html", "Ranking &amp; Shortlist") +
           tab("compare", "compare.html", "Compare") +
           tab("edit", "program-form.html", "Edit program");
  }
  document.getElementById("shell").innerHTML =
    '<header class="app-header"><a class="brand" href="programs.html">' +
    '<img src="EduMatchPH_logo.jpg" alt="">EduMatch PH</a>' +
    '<div class="who"><span id="org-name"></span><span id="admin-name"></span>' +
    '<button class="btn-secondary" id="logout-btn" type="button">Log out</button></div></header>' +
    '<nav class="subnav">' + nav + "</nav>";
  document.getElementById("logout-btn").addEventListener("click", logout);
  try {
    const me = await getMe();
    document.getElementById("admin-name").textContent = me.full_name;
    document.getElementById("org-name").textContent = String(me.organization_id).toUpperCase();
  } catch (err) { /* apiFetch already redirected to login if needed */ }
}

// Disable Run Screening / Run Ranking when the program is Closed.
function statusPill(status) {
  const cls = status === "Closed" ? "no" : status === "Open" ? "ok" : "neutral";
  return `<span class="pill ${cls}">${escapeHtml(status)}</span>`;
}
function programTitle(p) { return `${p.scholarship_name} (${p.provider || ""})`; }
