"""ポモドーロタイマーのロジック"""


class PomodoroTimer:
    """ポモドーロタイマークラス。

    25分の作業セッションと5分の休憩セッションを管理する。
    """

    DEFAULT_WORK_MINUTES = 25
    DEFAULT_BREAK_MINUTES = 5

    def __init__(self, work_minutes: int = DEFAULT_WORK_MINUTES, break_minutes: int = DEFAULT_BREAK_MINUTES):
        self.work_duration = work_minutes * 60
        self.break_duration = break_minutes * 60
        self.is_work_session = True
        self.is_running = False
        self.remaining = self.work_duration

    def start(self) -> None:
        """タイマーを開始する。"""
        self.is_running = True

    def pause(self) -> None:
        """タイマーを一時停止する。"""
        self.is_running = False

    def reset(self) -> None:
        """タイマーをリセットし、作業セッションの初期状態に戻す。"""
        self.is_running = False
        self.is_work_session = True
        self.remaining = self.work_duration

    def tick(self) -> bool:
        """1秒経過させる。

        Returns:
            bool: セッションが終了した場合は True、継続中は False。
        """
        if not self.is_running:
            return False

        if self.remaining > 0:
            self.remaining -= 1

        if self.remaining == 0:
            self.is_running = False
            return True

        return False

    def switch_session(self) -> None:
        """作業セッションと休憩セッションを切り替える。"""
        self.is_work_session = not self.is_work_session
        self.remaining = self.work_duration if self.is_work_session else self.break_duration
        self.is_running = False

    def get_display_time(self) -> str:
        """残り時間を MM:SS 形式の文字列で返す。"""
        minutes, seconds = divmod(self.remaining, 60)
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def session_label(self) -> str:
        """現在のセッション種別のラベルを返す。"""
        return "作業" if self.is_work_session else "休憩"
