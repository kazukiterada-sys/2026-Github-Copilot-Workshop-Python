"""PomodoroTimer のユニットテスト"""
import pytest
from timer import PomodoroTimer


def test_initial_state():
    """初期状態の確認。"""
    timer = PomodoroTimer()
    assert timer.remaining == 25 * 60
    assert timer.is_running is False
    assert timer.is_work_session is True
    assert timer.get_display_time() == "25:00"


def test_custom_durations():
    """カスタム時間の設定。"""
    timer = PomodoroTimer(work_minutes=10, break_minutes=3)
    assert timer.work_duration == 10 * 60
    assert timer.break_duration == 3 * 60
    assert timer.remaining == 10 * 60


def test_start():
    """start() でタイマーが開始される。"""
    timer = PomodoroTimer()
    timer.start()
    assert timer.is_running is True


def test_pause():
    """pause() でタイマーが停止される。"""
    timer = PomodoroTimer()
    timer.start()
    timer.pause()
    assert timer.is_running is False


def test_tick_decrements_remaining():
    """tick() で残り時間が1秒減る。"""
    timer = PomodoroTimer()
    timer.start()
    result = timer.tick()
    assert timer.remaining == 25 * 60 - 1
    assert result is False


def test_tick_when_not_running():
    """停止中は tick() しても時間が変わらない。"""
    timer = PomodoroTimer()
    initial = timer.remaining
    result = timer.tick()
    assert timer.remaining == initial
    assert result is False


def test_tick_session_ends():
    """残り0になったときに tick() が True を返す。"""
    timer = PomodoroTimer(work_minutes=1, break_minutes=1)
    timer.start()
    # 59秒進める
    for _ in range(59):
        result = timer.tick()
        assert result is False
    # 最後の1秒
    result = timer.tick()
    assert result is True
    assert timer.remaining == 0
    assert timer.is_running is False


def test_reset():
    """reset() で初期状態に戻る。"""
    timer = PomodoroTimer()
    timer.start()
    for _ in range(10):
        timer.tick()
    timer.reset()
    assert timer.remaining == 25 * 60
    assert timer.is_running is False
    assert timer.is_work_session is True


def test_get_display_time_format():
    """get_display_time() の出力形式。"""
    timer = PomodoroTimer()
    assert timer.get_display_time() == "25:00"
    timer.remaining = 90
    assert timer.get_display_time() == "01:30"
    timer.remaining = 5
    assert timer.get_display_time() == "00:05"


def test_switch_session_to_break():
    """switch_session() で休憩セッションに切り替わる。"""
    timer = PomodoroTimer()
    timer.switch_session()
    assert timer.is_work_session is False
    assert timer.remaining == timer.break_duration
    assert timer.is_running is False


def test_switch_session_back_to_work():
    """switch_session() を2回呼ぶと作業セッションに戻る。"""
    timer = PomodoroTimer()
    timer.switch_session()
    timer.switch_session()
    assert timer.is_work_session is True
    assert timer.remaining == timer.work_duration


def test_session_label():
    """session_label プロパティ。"""
    timer = PomodoroTimer()
    assert timer.session_label == "作業"
    timer.switch_session()
    assert timer.session_label == "休憩"
