/**
 * Pomodoro Timer – timer.js
 * Handles API communication, countdown, circular progress,
 * cycle dots, and dark/light theme toggle.
 */

const CIRCUMFERENCE = 2 * Math.PI * 88; // matches SVG r="88"

const elTime = document.getElementById("timer-time");
const elMode = document.getElementById("mode-label");
const elRing = document.getElementById("ring-progress");
const elDots = document.querySelectorAll(".dot");
const elTotal = document.querySelector("#total-cycles strong");
const btnStart = document.getElementById("btn-start");
const btnStop = document.getElementById("btn-stop");
const btnReset = document.getElementById("btn-reset");
const btnTheme = document.getElementById("theme-toggle");
const htmlEl = document.documentElement;

const MODE_LABELS = {
  work:        "集中時間",
  short_break: "短い休憩",
  long_break:  "長い休憩",
};

let pollTimeout = null;

// ---------- Ring progress ----------

function setRingProgress(remaining, total) {
  const ratio = total > 0 ? remaining / total : 1;
  const offset = CIRCUMFERENCE * (1 - ratio);
  elRing.style.strokeDasharray = CIRCUMFERENCE;
  elRing.style.strokeDashoffset = offset;
}

// ---------- Format time ----------

function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

// ---------- Update UI from status ----------

function applyStatus(data) {
  elTime.textContent = formatTime(data.remaining);
  elMode.textContent = MODE_LABELS[data.mode] || data.mode;
  setRingProgress(data.remaining, data.total);

  // Set mode color on body
  document.body.setAttribute("data-mode", data.mode);

  // Cycle dots: filled = completed cycles in current set, active = current
  elDots.forEach((dot, i) => {
    dot.classList.remove("done", "active");
    if (i < data.cycle) {
      dot.classList.add("done");
    } else if (i === data.cycle && data.mode === "work") {
      dot.classList.add("active");
    }
  });

  elTotal.textContent = data.total_cycles;

  // Buttons
  btnStart.disabled = data.running;
  btnStop.disabled = !data.running;
}

// ---------- API helpers ----------

async function apiPost(path) {
  const res = await fetch(path, { method: "POST" });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

async function apiGet(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

// ---------- Polling ----------

function startPolling() {
  if (pollTimeout !== null) return;
  schedulePoll();
}

function schedulePoll() {
  pollTimeout = setTimeout(async () => {
    pollTimeout = null;
    try {
      const data = await apiGet("/api/status");
      applyStatus(data);
      if (data.running) schedulePoll();
    } catch (err) {
      console.error("Poll error:", err);
    }
  }, 500);
}

function stopPolling() {
  clearTimeout(pollTimeout);
  pollTimeout = null;
}

// ---------- Button handlers ----------

btnStart.addEventListener("click", async () => {
  try {
    const data = await apiPost("/api/start");
    applyStatus(data);
    startPolling();
  } catch (err) {
    console.error("Start error:", err);
  }
});

btnStop.addEventListener("click", async () => {
  try {
    const data = await apiPost("/api/stop");
    applyStatus(data);
    stopPolling();
  } catch (err) {
    console.error("Stop error:", err);
  }
});

btnReset.addEventListener("click", async () => {
  stopPolling();
  try {
    const data = await apiPost("/api/reset");
    applyStatus(data);
  } catch (err) {
    console.error("Reset error:", err);
  }
});

// ---------- Theme toggle ----------

function applyTheme(theme) {
  htmlEl.setAttribute("data-theme", theme);
  btnTheme.querySelector(".theme-icon").textContent = theme === "dark" ? "☀️" : "🌙";
  localStorage.setItem("pomo-theme", theme);
}

btnTheme.addEventListener("click", () => {
  const current = htmlEl.getAttribute("data-theme");
  applyTheme(current === "dark" ? "light" : "dark");
});

// ---------- Init ----------

(async () => {
  // Restore saved theme
  const savedTheme = localStorage.getItem("pomo-theme") || "light";
  applyTheme(savedTheme);

  // Load current server state
  try {
    const data = await apiGet("/api/status");
    applyStatus(data);
    if (data.running) startPolling();
  } catch (err) {
    console.error("Init error:", err);
  }
})();
