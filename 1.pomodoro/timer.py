# タイマーのロジック（ポモドーロタイマー）

class PomodoroTimer:
    def __init__(self, work_minutes=25, short_break_minutes=5, long_break_minutes=15, cycles=4):
        self.work_seconds = work_minutes * 60
        self.short_break_seconds = short_break_minutes * 60
        self.long_break_seconds = long_break_minutes * 60
        self.cycles = cycles
        self.current_cycle = 0
        self.state = 'stopped'  # 'work', 'short_break', 'long_break', 'stopped'
        self.remaining_seconds = self.work_seconds

    def start(self):
        if self.state == 'stopped':
            self.state = 'work'
            self.remaining_seconds = self.work_seconds
        elif self.state in ['work', 'short_break', 'long_break']:
            pass  # すでに進行中

    def stop(self):
        self.state = 'stopped'

    def reset(self):
        self.current_cycle = 0
        self.state = 'stopped'
        self.remaining_seconds = self.work_seconds

    def tick(self):
        if self.state == 'stopped':
            return
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
        if self.remaining_seconds == 0:
            if self.state == 'work':
                self.current_cycle += 1
                if self.current_cycle % self.cycles == 0:
                    self.state = 'long_break'
                    self.remaining_seconds = self.long_break_seconds
                else:
                    self.state = 'short_break'
                    self.remaining_seconds = self.short_break_seconds
            elif self.state == 'short_break':
                self.state = 'work'
                self.remaining_seconds = self.work_seconds
            elif self.state == 'long_break':
                self.state = 'work'
                self.remaining_seconds = self.work_seconds

    def get_status(self):
        return {
            'state': self.state,
            'remaining_seconds': self.remaining_seconds,
            'current_cycle': self.current_cycle
        }
