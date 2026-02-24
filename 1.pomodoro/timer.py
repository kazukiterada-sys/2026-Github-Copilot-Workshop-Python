"""
ポモドーロタイマーのコアロジック（GUI非依存）。

PomodoroSettings と PomodoroTimer を提供します。
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

WORK_TIME_OPTIONS = [15, 25, 35, 45]   # 分
BREAK_TIME_OPTIONS = [5, 10, 15]        # 分

THEMES: dict[str, dict[str, str]] = {
    "ライト": {
        "bg": "#FFFFFF",
        "fg": "#222222",
        "accent": "#E74C3C",
        "btn_bg": "#F0F0F0",
        "btn_fg": "#222222",
        "timer_fg": "#E74C3C",
    },
    "ダーク": {
        "bg": "#1E1E1E",
        "fg": "#EEEEEE",
        "accent": "#E74C3C",
        "btn_bg": "#333333",
        "btn_fg": "#EEEEEE",
        "timer_fg": "#FF6B6B",
    },
    "集中": {
        "bg": "#F5F5F0",
        "fg": "#333333",
        "accent": "#555555",
        "btn_bg": "#E8E8E3",
        "btn_fg": "#333333",
        "timer_fg": "#333333",
    },
}


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@dataclass
class PomodoroSettings:
    """ユーザーが変更できる設定を保持するデータクラス。"""

    work_minutes: int = 25
    break_minutes: int = 5
    theme: str = "ライト"
    sound_start: bool = True
    sound_end: bool = True
    sound_tick: bool = False

    def validate(self) -> None:
        """設定値の妥当性を検証する。"""
        if self.work_minutes not in WORK_TIME_OPTIONS:
            raise ValueError(
                f"作業時間は {WORK_TIME_OPTIONS} のいずれかを指定してください。"
            )
        if self.break_minutes not in BREAK_TIME_OPTIONS:
            raise ValueError(
                f"休憩時間は {BREAK_TIME_OPTIONS} のいずれかを指定してください。"
            )
        if self.theme not in THEMES:
            raise ValueError(
                f"テーマは {list(THEMES.keys())} のいずれかを指定してください。"
            )


# ---------------------------------------------------------------------------
# Timer Logic
# ---------------------------------------------------------------------------


class PomodoroTimer:
    """ポモドーロタイマーのロジックを担うクラス（GUI非依存）。"""

    def __init__(self, settings: PomodoroSettings) -> None:
        self.settings = settings
        self._reset_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """タイマーを開始する。"""
        if not self.running:
            self.running = True

    def pause(self) -> None:
        """タイマーを一時停止する。"""
        self.running = False

    def reset(self) -> None:
        """タイマーをリセットする。"""
        self._reset_state()

    def tick(self) -> bool:
        """1秒経過を処理する。残り時間が0になった場合 True を返す。"""
        if not self.running:
            return False
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
        if self.remaining_seconds == 0:
            self.running = False
            return True
        return False

    def next_phase(self) -> None:
        """作業↔休憩フェーズを切り替える。"""
        if self.phase == "work":
            self.phase = "break"
            self.remaining_seconds = self.settings.break_minutes * 60
        else:
            self.phase = "work"
            self.session_count += 1
            self.remaining_seconds = self.settings.work_minutes * 60
        self.running = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def display_time(self) -> str:
        """MM:SS 形式の残り時間文字列を返す。"""
        mins, secs = divmod(self.remaining_seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    @property
    def phase_label(self) -> str:
        """現在のフェーズ名を返す。"""
        return "🍅 作業中" if self.phase == "work" else "☕ 休憩中"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        self.phase: str = "work"
        self.remaining_seconds: int = self.settings.work_minutes * 60
        self.running: bool = False
        self.session_count: int = 0
