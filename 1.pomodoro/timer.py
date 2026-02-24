"""Pomodoro Timer logic."""

import time
import threading


class PomodoroTimer:
    """Manages pomodoro timer state and transitions."""

    WORK_DURATION = 25 * 60       # 25 minutes
    SHORT_BREAK = 5 * 60          # 5 minutes
    LONG_BREAK = 15 * 60          # 15 minutes
    CYCLES_BEFORE_LONG_BREAK = 4

    def __init__(self):
        self.reset()
        self._lock = threading.Lock()
        self._thread = None

    def reset(self):
        """Reset the timer to the initial state."""
        self.mode = "work"          # "work" | "short_break" | "long_break"
        self.remaining = self.WORK_DURATION
        self.total = self.WORK_DURATION
        self.running = False
        self.cycle = 0              # completed work cycles (0-3)
        self.total_cycles = 0       # total completed work sessions
        self._stop_event = threading.Event()

    def start(self):
        """Start or resume the timer."""
        with self._lock:
            if self.running:
                return
            self.running = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        """Pause the timer."""
        with self._lock:
            if not self.running:
                return
            self.running = False
            self._stop_event.set()

    def _run(self):
        """Background countdown thread."""
        while True:
            with self._lock:
                if self._stop_event.is_set() or self.remaining <= 0:
                    break
            self._stop_event.wait(1)
            if not self._stop_event.is_set():
                with self._lock:
                    self.remaining -= 1
                    if self.remaining <= 0:
                        self._on_complete()

    def _on_complete(self):
        """Handle timer completion and cycle transitions."""
        self.running = False
        self._stop_event.set()
        if self.mode == "work":
            self.total_cycles += 1
            self.cycle = (self.cycle + 1) % self.CYCLES_BEFORE_LONG_BREAK
            if self.cycle == 0:
                self.mode = "long_break"
                self.remaining = self.LONG_BREAK
                self.total = self.LONG_BREAK
            else:
                self.mode = "short_break"
                self.remaining = self.SHORT_BREAK
                self.total = self.SHORT_BREAK
        else:
            self.mode = "work"
            self.remaining = self.WORK_DURATION
            self.total = self.WORK_DURATION

    def status(self):
        """Return current timer status as a dict."""
        with self._lock:
            return {
                "mode": self.mode,
                "remaining": self.remaining,
                "total": self.total,
                "running": self.running,
                "cycle": self.cycle,
                "total_cycles": self.total_cycles,
            }
