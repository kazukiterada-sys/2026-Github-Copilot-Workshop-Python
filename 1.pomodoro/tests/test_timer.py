import unittest
from timer import PomodoroTimer

class TestPomodoroTimer(unittest.TestCase):
    def setUp(self):
        self.timer = PomodoroTimer(work_minutes=1, short_break_minutes=1, long_break_minutes=2, cycles=2)

    def test_initial_state(self):
        status = self.timer.get_status()
        self.assertEqual(status['state'], 'stopped')
        self.assertEqual(status['remaining_seconds'], 60)
        self.assertEqual(status['current_cycle'], 0)

    def test_start_and_tick(self):
        self.timer.start()
        self.assertEqual(self.timer.state, 'work')
        for _ in range(60):
            self.timer.tick()
        self.assertEqual(self.timer.state, 'short_break')
        self.assertEqual(self.timer.current_cycle, 1)

    def test_cycle_to_long_break(self):
        self.timer.start()
        for _ in range(60):
            self.timer.tick()
        for _ in range(60):
            self.timer.tick()
        for _ in range(60):
            self.timer.tick()
        self.assertEqual(self.timer.state, 'long_break')
        self.assertEqual(self.timer.current_cycle, 2)

    def test_reset(self):
        self.timer.start()
        self.timer.tick()
        self.timer.reset()
        status = self.timer.get_status()
        self.assertEqual(status['state'], 'stopped')
        self.assertEqual(status['remaining_seconds'], 60)
        self.assertEqual(status['current_cycle'], 0)

if __name__ == '__main__':
    unittest.main()
