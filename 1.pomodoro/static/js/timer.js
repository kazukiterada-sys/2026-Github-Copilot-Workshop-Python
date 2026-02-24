(function (global) {
    function formatTime(totalSeconds) {
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    }

    function getNextPhase(state, currentCycle, cycles, durations) {
        if (state === "work") {
            const nextCycle = currentCycle + 1;
            if (nextCycle % cycles === 0) {
                return {
                    state: "long_break",
                    currentCycle: nextCycle,
                    remainingSeconds: durations.longBreak,
                };
            }
            return {
                state: "short_break",
                currentCycle: nextCycle,
                remainingSeconds: durations.shortBreak,
            };
        }

        return {
            state: "work",
            currentCycle,
            remainingSeconds: durations.work,
        };
    }

    function createTimerEngine(options) {
        const config = {
            work: (options?.workMinutes ?? 25) * 60,
            shortBreak: (options?.shortBreakMinutes ?? 5) * 60,
            longBreak: (options?.longBreakMinutes ?? 15) * 60,
            cycles: options?.cycles ?? 4,
        };

        const state = {
            status: "stopped",
            phase: "work",
            remainingSeconds: config.work,
            currentCycle: 0,
        };

        function start() {
            if (state.status === "stopped") {
                state.status = "running";
            }
        }

        function stop() {
            state.status = "stopped";
        }

        function reset() {
            state.status = "stopped";
            state.phase = "work";
            state.remainingSeconds = config.work;
            state.currentCycle = 0;
        }

        function tick() {
            if (state.status !== "running") {
                return;
            }
            if (state.remainingSeconds > 0) {
                state.remainingSeconds -= 1;
            }
            if (state.remainingSeconds === 0) {
                const next = getNextPhase(state.phase, state.currentCycle, config.cycles, config);
                state.phase = next.state;
                state.currentCycle = next.currentCycle;
                state.remainingSeconds = next.remainingSeconds;
            }
        }

        function getStatusText() {
            if (state.status === "stopped") {
                return "停止中";
            }
            if (state.phase === "work") {
                return "作業中";
            }
            if (state.phase === "short_break") {
                return "短い休憩中";
            }
            return "長い休憩中";
        }

        function getProgressPercent() {
            const phaseTotal = state.phase === "work"
                ? config.work
                : state.phase === "short_break"
                    ? config.shortBreak
                    : config.longBreak;
            return Math.floor(((phaseTotal - state.remainingSeconds) / phaseTotal) * 100);
        }

        return {
            start,
            stop,
            reset,
            tick,
            getState: () => ({ ...state }),
            getStatusText,
            getProgressPercent,
            formatTime,
        };
    }

    function calculateProgressPercent(timerState) {
        const settings = timerState.settings;
        const phaseTotal = timerState.state === "work"
            ? settings.work_minutes * 60
            : timerState.state === "short_break"
                ? settings.short_break_minutes * 60
                : settings.long_break_minutes * 60;
        if (phaseTotal <= 0) {
            return 0;
        }
        return Math.floor(((phaseTotal - timerState.remaining_seconds) / phaseTotal) * 100);
    }

    async function fetchJSON(url, method) {
        const response = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
        });
        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }
        return response.json();
    }

    function applyTheme(doc) {
        const saved = localStorage.getItem("theme");
        if (saved === "dark") {
            doc.body.classList.add("dark");
        }
    }

    function toggleTheme(doc) {
        doc.body.classList.toggle("dark");
        const value = doc.body.classList.contains("dark") ? "dark" : "light";
        localStorage.setItem("theme", value);
    }

    function bindUI(doc) {
        const timeEl = doc.getElementById("time");
        const statusEl = doc.getElementById("status");
        const cycleEl = doc.getElementById("cycle-count");
        const progressEl = doc.getElementById("progress");
        const progressTextEl = doc.getElementById("progress-text");
        const completedEl = doc.getElementById("completed-count");
        const themeButton = doc.getElementById("theme-toggle");

        let running = false;

        function render(state) {
            timeEl.textContent = formatTime(state.remaining_seconds);
            statusEl.textContent = `状態: ${state.label}`;
            cycleEl.textContent = String(state.current_cycle);
            const progress = calculateProgressPercent(state);
            progressEl.value = progress;
            progressTextEl.textContent = `${progress}%`;
            completedEl.textContent = String(state.completed_pomodoros);
            running = state.state !== "stopped";
        }

        async function refreshStatus() {
            const state = await fetchJSON("/api/timer/status", "GET");
            render(state);
        }

        async function control(url) {
            const state = await fetchJSON(url, "POST");
            render(state);
        }

        themeButton.addEventListener("click", () => toggleTheme(doc));

        doc.getElementById("start").addEventListener("click", async () => {
            await control("/api/timer/start");
        });
        doc.getElementById("stop").addEventListener("click", async () => {
            await control("/api/timer/stop");
        });
        doc.getElementById("reset").addEventListener("click", async () => {
            await control("/api/timer/reset");
        });

        setInterval(async () => {
            if (!running) {
                return;
            }
            const state = await fetchJSON("/api/timer/tick", "POST");
            render(state);
        }, 1000);

        applyTheme(doc);
        refreshStatus();
    }

    const api = {
        formatTime,
        getNextPhase,
        createTimerEngine,
        calculateProgressPercent,
    };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = api;
    }

    global.PomodoroTimer = api;

    if (typeof window !== "undefined" && window.document) {
        window.addEventListener("DOMContentLoaded", () => {
            bindUI(window.document);
        });
    }
})(typeof window !== "undefined" ? window : globalThis);
