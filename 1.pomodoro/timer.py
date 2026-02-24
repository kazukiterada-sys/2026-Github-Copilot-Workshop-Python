# Pomodoro Timer Logic


class PomodoroTimer:
    def __init__(self, work_duration=25 * 60, short_break=5 * 60, long_break=15 * 60):
        self.work_duration = work_duration
        self.short_break = short_break
        self.long_break = long_break

        self.is_running = False
        self.is_break = False
        self.time_remaining = work_duration
        self.cycle_count = 0

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def reset(self):
        self.is_running = False
        self.is_break = False
        self.time_remaining = self.work_duration
        self.cycle_count = 0

    def get_status(self):
        return {
            "is_running": self.is_running,
            "is_break": self.is_break,
            "time_remaining": self.time_remaining,
            "cycle_count": self.cycle_count,
        }

    def tick(self):
        """Decrement time by 1 second. Handle transitions between work/break."""
        if not self.is_running:
            return

        if self.time_remaining > 0:
            self.time_remaining -= 1
        else:
            # Transition
            if not self.is_break:
                # Work session just ended
                self.cycle_count += 1
                self.is_break = True
                if self.cycle_count % 4 == 0:
                    self.time_remaining = self.long_break
                else:
                    self.time_remaining = self.short_break
            else:
                # Break just ended, start new work session
                self.is_break = False
                self.time_remaining = self.work_duration
