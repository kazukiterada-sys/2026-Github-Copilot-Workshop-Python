import pytest
from timer import PomodoroTimer


@pytest.fixture
def timer():
    return PomodoroTimer()


def test_initial_state(timer):
    assert timer.is_running is False
    assert timer.is_break is False
    assert timer.time_remaining == 25 * 60
    assert timer.cycle_count == 0


def test_initial_work_duration(timer):
    assert timer.work_duration == 25 * 60


def test_initial_short_break(timer):
    assert timer.short_break == 5 * 60


def test_initial_long_break(timer):
    assert timer.long_break == 15 * 60


def test_start(timer):
    timer.start()
    assert timer.is_running is True


def test_stop(timer):
    timer.start()
    timer.stop()
    assert timer.is_running is False


def test_reset(timer):
    timer.start()
    timer.tick()
    timer.reset()
    assert timer.is_running is False
    assert timer.is_break is False
    assert timer.time_remaining == timer.work_duration
    assert timer.cycle_count == 0


def test_tick_decrements_time(timer):
    timer.start()
    initial_time = timer.time_remaining
    timer.tick()
    assert timer.time_remaining == initial_time - 1


def test_tick_does_not_decrement_when_stopped(timer):
    initial_time = timer.time_remaining
    timer.tick()
    assert timer.time_remaining == initial_time


def test_tick_multiple_times(timer):
    timer.start()
    for _ in range(10):
        timer.tick()
    assert timer.time_remaining == 25 * 60 - 10


def test_get_status_returns_dict(timer):
    status = timer.get_status()
    assert isinstance(status, dict)
    assert 'is_running' in status
    assert 'is_break' in status
    assert 'time_remaining' in status
    assert 'cycle_count' in status


def test_get_status_values(timer):
    timer.start()
    status = timer.get_status()
    assert status['is_running'] is True
    assert status['is_break'] is False
    assert status['time_remaining'] == 25 * 60
    assert status['cycle_count'] == 0


def test_work_to_break_transition(timer):
    timer.start()
    # Run down to 0 then tick to trigger transition
    timer.time_remaining = 0
    timer.tick()
    assert timer.is_break is True
    assert timer.cycle_count == 1
    assert timer.time_remaining == timer.short_break


def test_break_to_work_transition(timer):
    timer.start()
    timer.time_remaining = 0
    timer.tick()  # Now in short break
    timer.time_remaining = 0
    timer.tick()  # Now back to work
    assert timer.is_break is False
    assert timer.time_remaining == timer.work_duration


def test_long_break_after_4_cycles(timer):
    timer.start()
    # Complete 3 work sessions with short breaks (cycles 1, 2, 3)
    for _ in range(3):
        timer.time_remaining = 0
        timer.tick()  # End of work -> short break
        assert timer.time_remaining == timer.short_break
        timer.time_remaining = 0
        timer.tick()  # End of break -> work
    # 4th work session ends -> should trigger long break
    timer.time_remaining = 0
    timer.tick()
    assert timer.is_break is True
    assert timer.time_remaining == timer.long_break


def test_cycle_count_increments(timer):
    timer.start()
    timer.time_remaining = 0
    timer.tick()
    assert timer.cycle_count == 1
    timer.time_remaining = 0
    timer.tick()  # break ends
    timer.time_remaining = 0
    timer.tick()  # work ends
    assert timer.cycle_count == 2


def test_custom_durations():
    t = PomodoroTimer(work_duration=10, short_break=5, long_break=15)
    assert t.work_duration == 10
    assert t.short_break == 5
    assert t.long_break == 15
    assert t.time_remaining == 10
