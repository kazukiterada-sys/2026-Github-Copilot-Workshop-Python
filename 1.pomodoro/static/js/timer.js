/**
 * Pomodoro Timer - Frontend Logic
 * Stage 2: Countdown, button operations, cycle tracking
 */

const DURATIONS = {
  work: 25 * 60,
  shortBreak: 5 * 60,
  longBreak: 15 * 60,
};

const LONG_BREAK_INTERVAL = 4;

class PomodoroTimer {
  constructor() {
    this.state = "idle"; // idle | running | paused
    this.sessionType = "work"; // work | shortBreak | longBreak
    this.timeRemaining = DURATIONS.work;
    this.completedCycles = 0;
    this._intervalId = null;
    this._onTick = null;
    this._onSessionEnd = null;
  }

  get formattedTime() {
    const minutes = Math.floor(this.timeRemaining / 60);
    const seconds = this.timeRemaining % 60;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }

  get progress() {
    const total = DURATIONS[this.sessionType];
    return total > 0 ? (total - this.timeRemaining) / total : 0;
  }

  onTick(callback) {
    this._onTick = callback;
  }

  onSessionEnd(callback) {
    this._onSessionEnd = callback;
  }

  start() {
    if (this.state === "running") return;
    this.state = "running";
    this._intervalId = setInterval(() => this._tick(), 1000);
  }

  pause() {
    if (this.state !== "running") return;
    this.state = "paused";
    clearInterval(this._intervalId);
    this._intervalId = null;
  }

  reset() {
    this.state = "idle";
    clearInterval(this._intervalId);
    this._intervalId = null;
    this.timeRemaining = DURATIONS[this.sessionType];
    if (this._onTick) this._onTick();
  }

  _tick() {
    if (this.timeRemaining > 0) {
      this.timeRemaining -= 1;
      if (this._onTick) this._onTick();
      if (this.timeRemaining === 0) {
        this._endSession();
      }
    }
  }

  _endSession() {
    clearInterval(this._intervalId);
    this._intervalId = null;
    this.state = "idle";

    if (this.sessionType === "work") {
      this.completedCycles += 1;
    }

    const nextSession = this._getNextSession();
    if (this._onSessionEnd) this._onSessionEnd(this.sessionType, nextSession);

    this.sessionType = nextSession;
    this.timeRemaining = DURATIONS[nextSession];
  }

  _getNextSession() {
    if (this.sessionType !== "work") return "work";
    if (this.completedCycles % LONG_BREAK_INTERVAL === 0 && this.completedCycles > 0) {
      return "longBreak";
    }
    return "shortBreak";
  }
}

// UI Controller (only executes in browser environment)
function initUI(timer) {
  const timeDisplay = document.getElementById("time-display");
  const sessionLabel = document.getElementById("session-label");
  const startPauseBtn = document.getElementById("start-pause-btn");
  const resetBtn = document.getElementById("reset-btn");
  const cycleIndicators = document.querySelectorAll(".cycle-dot");
  const progressBar = document.getElementById("progress-bar");

  const SESSION_LABELS = {
    work: "集中タイム",
    shortBreak: "短い休憩",
    longBreak: "長い休憩",
  };

  function updateDisplay() {
    timeDisplay.textContent = timer.formattedTime;
    sessionLabel.textContent = SESSION_LABELS[timer.sessionType];
    startPauseBtn.textContent = timer.state === "running" ? "一時停止" : "スタート";

    const progressPercent = Math.round(timer.progress * 100);
    if (progressBar) {
      progressBar.style.width = `${progressPercent}%`;
    }

    const cyclePosition = timer.completedCycles % LONG_BREAK_INTERVAL;
    cycleIndicators.forEach((dot, index) => {
      dot.classList.toggle("completed", index < cyclePosition);
      dot.classList.toggle(
        "current",
        index === cyclePosition && timer.sessionType === "work"
      );
    });
  }

  timer.onTick(updateDisplay);

  timer.onSessionEnd((endedSession, nextSession) => {
    updateDisplay();
    const label = SESSION_LABELS[nextSession];
    const message = `${SESSION_LABELS[endedSession]}が終了しました！次は「${label}」です。`;
    if (typeof alert !== "undefined") alert(message);
  });

  startPauseBtn.addEventListener("click", () => {
    if (timer.state === "running") {
      timer.pause();
    } else {
      timer.start();
    }
    updateDisplay();
  });

  resetBtn.addEventListener("click", () => {
    timer.reset();
    updateDisplay();
  });

  updateDisplay();
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { PomodoroTimer, DURATIONS, LONG_BREAK_INTERVAL };
} else if (typeof window !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    const timer = new PomodoroTimer();
    initUI(timer);
  });
}
