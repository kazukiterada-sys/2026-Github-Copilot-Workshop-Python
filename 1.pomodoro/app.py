# Pomodoro Timer App
"""
ポモドーロタイマーアプリ
カスタマイズ機能：
  - 作業時間：15/25/35/45分から選択
  - 休憩時間：5/10/15分から選択
  - テーマ：ダーク／ライト／集中（ミニマル）
  - サウンド：開始音・終了音・tick音のオン／オフ
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from timer import (
    BREAK_TIME_OPTIONS,
    THEMES,
    WORK_TIME_OPTIONS,
    PomodoroSettings,
    PomodoroTimer,
)


# ---------------------------------------------------------------------------
# GUI Application
# ---------------------------------------------------------------------------


class PomodoroApp(tk.Tk):
    """ポモドーロタイマーの Tkinter GUI アプリケーション。"""

    def __init__(self, settings: PomodoroSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or PomodoroSettings()
        self.settings.validate()
        self.timer = PomodoroTimer(self.settings)

        self.title("🍅 ポモドーロタイマー")
        self.resizable(False, False)

        self._build_ui()
        self._apply_theme()
        self._update_display()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """ウィジェットを構築する。"""
        self._frame_main = tk.Frame(self, padx=20, pady=20)
        self._frame_main.pack(fill=tk.BOTH, expand=True)

        # フェーズラベル
        self._lbl_phase = tk.Label(
            self._frame_main, text="", font=("Helvetica", 16, "bold")
        )
        self._lbl_phase.pack(pady=(0, 4))

        # タイマー表示
        self._lbl_timer = tk.Label(
            self._frame_main, text="00:00", font=("Helvetica", 60, "bold")
        )
        self._lbl_timer.pack()

        # セッション数
        self._lbl_session = tk.Label(
            self._frame_main, text="セッション数: 0", font=("Helvetica", 10)
        )
        self._lbl_session.pack(pady=(4, 10))

        # 制御ボタン行
        self._frame_btns = tk.Frame(self._frame_main)
        self._frame_btns.pack(pady=(0, 16))

        self._btn_start = tk.Button(
            self._frame_btns,
            text="▶ 開始",
            width=9,
            command=self._on_start_pause,
        )
        self._btn_start.grid(row=0, column=0, padx=4)

        self._btn_reset = tk.Button(
            self._frame_btns, text="↺ リセット", width=9, command=self._on_reset
        )
        self._btn_reset.grid(row=0, column=1, padx=4)

        self._btn_skip = tk.Button(
            self._frame_btns,
            text="⏭ スキップ",
            width=9,
            command=self._on_skip,
        )
        self._btn_skip.grid(row=0, column=2, padx=4)

        # 設定エリア（区切り線＋オプション）
        ttk.Separator(self._frame_main, orient="horizontal").pack(
            fill=tk.X, pady=(0, 12)
        )
        self._build_settings_ui()

    def _build_settings_ui(self) -> None:
        """設定エリアのウィジェットを構築する。"""
        frame = tk.Frame(self._frame_main)
        frame.pack(fill=tk.X)

        # --- 作業時間 ---
        tk.Label(frame, text="作業時間(分):", font=("Helvetica", 10)).grid(
            row=0, column=0, sticky="w", pady=2
        )
        self._var_work = tk.IntVar(value=self.settings.work_minutes)
        cb_work = ttk.Combobox(
            frame,
            textvariable=self._var_work,
            values=WORK_TIME_OPTIONS,
            state="readonly",
            width=6,
        )
        cb_work.grid(row=0, column=1, sticky="w", padx=4, pady=2)
        cb_work.bind("<<ComboboxSelected>>", self._on_work_time_change)

        # --- 休憩時間 ---
        tk.Label(frame, text="休憩時間(分):", font=("Helvetica", 10)).grid(
            row=1, column=0, sticky="w", pady=2
        )
        self._var_break = tk.IntVar(value=self.settings.break_minutes)
        cb_break = ttk.Combobox(
            frame,
            textvariable=self._var_break,
            values=BREAK_TIME_OPTIONS,
            state="readonly",
            width=6,
        )
        cb_break.grid(row=1, column=1, sticky="w", padx=4, pady=2)
        cb_break.bind("<<ComboboxSelected>>", self._on_break_time_change)

        # --- テーマ ---
        tk.Label(frame, text="テーマ:", font=("Helvetica", 10)).grid(
            row=2, column=0, sticky="w", pady=2
        )
        self._var_theme = tk.StringVar(value=self.settings.theme)
        cb_theme = ttk.Combobox(
            frame,
            textvariable=self._var_theme,
            values=list(THEMES.keys()),
            state="readonly",
            width=10,
        )
        cb_theme.grid(row=2, column=1, sticky="w", padx=4, pady=2)
        cb_theme.bind("<<ComboboxSelected>>", self._on_theme_change)

        # --- サウンド設定 ---
        tk.Label(frame, text="サウンド:", font=("Helvetica", 10)).grid(
            row=3, column=0, sticky="w", pady=2
        )
        sound_frame = tk.Frame(frame)
        sound_frame.grid(row=3, column=1, sticky="w", padx=4)

        self._var_sound_start = tk.BooleanVar(value=self.settings.sound_start)
        tk.Checkbutton(
            sound_frame,
            text="開始",
            variable=self._var_sound_start,
            command=self._on_sound_change,
        ).pack(side=tk.LEFT)

        self._var_sound_end = tk.BooleanVar(value=self.settings.sound_end)
        tk.Checkbutton(
            sound_frame,
            text="終了",
            variable=self._var_sound_end,
            command=self._on_sound_change,
        ).pack(side=tk.LEFT)

        self._var_sound_tick = tk.BooleanVar(value=self.settings.sound_tick)
        tk.Checkbutton(
            sound_frame,
            text="tick",
            variable=self._var_sound_tick,
            command=self._on_sound_change,
        ).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_start_pause(self) -> None:
        if self.timer.running:
            self.timer.pause()
            self._btn_start.config(text="▶ 開始")
        else:
            if self.settings.sound_start:
                self._play_sound("start")
            self.timer.start()
            self._btn_start.config(text="⏸ 一時停止")
            self._tick()

    def _on_reset(self) -> None:
        self.timer.reset()
        self._btn_start.config(text="▶ 開始")
        self._update_display()

    def _on_skip(self) -> None:
        self.timer.next_phase()
        self._btn_start.config(text="▶ 開始")
        self._update_display()

    def _on_work_time_change(self, _event: object = None) -> None:
        self.settings.work_minutes = self._var_work.get()
        if self.timer.phase == "work":
            self.timer.reset()
            self._update_display()

    def _on_break_time_change(self, _event: object = None) -> None:
        self.settings.break_minutes = self._var_break.get()
        if self.timer.phase == "break":
            self.timer.remaining_seconds = self.settings.break_minutes * 60
            self._update_display()

    def _on_theme_change(self, _event: object = None) -> None:
        self.settings.theme = self._var_theme.get()
        self._apply_theme()

    def _on_sound_change(self) -> None:
        self.settings.sound_start = self._var_sound_start.get()
        self.settings.sound_end = self._var_sound_end.get()
        self.settings.sound_tick = self._var_sound_tick.get()

    # ------------------------------------------------------------------
    # Timer loop
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        """1秒ごとに呼ばれるコールバック。"""
        if not self.timer.running:
            return

        finished = self.timer.tick()
        self._update_display()

        if self.settings.sound_tick:
            self._play_sound("tick")

        if finished:
            if self.settings.sound_end:
                self._play_sound("end")
            self._btn_start.config(text="▶ 開始")
            self.timer.next_phase()
            self._update_display()
        else:
            self.after(1000, self._tick)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def _update_display(self) -> None:
        self._lbl_timer.config(text=self.timer.display_time)
        self._lbl_phase.config(text=self.timer.phase_label)
        self._lbl_session.config(
            text=f"セッション数: {self.timer.session_count}"
        )

    def _apply_theme(self) -> None:
        """選択中のテーマを全ウィジェットに適用する。"""
        t = THEMES[self.settings.theme]
        bg = t["bg"]
        fg = t["fg"]
        btn_bg = t["btn_bg"]
        btn_fg = t["btn_fg"]
        timer_fg = t["timer_fg"]

        self.config(bg=bg)
        self._frame_main.config(bg=bg)

        self._lbl_phase.config(bg=bg, fg=fg)
        self._lbl_timer.config(bg=bg, fg=timer_fg)
        self._lbl_session.config(bg=bg, fg=fg)
        self._frame_btns.config(bg=bg)

        for btn in (self._btn_start, self._btn_reset, self._btn_skip):
            btn.config(bg=btn_bg, fg=btn_fg, activebackground=t["accent"])

        self._apply_theme_to_children(self._frame_main, bg, fg, btn_bg, btn_fg)

    def _apply_theme_to_children(
        self,
        widget: tk.Widget,
        bg: str,
        fg: str,
        btn_bg: str,
        btn_fg: str,
    ) -> None:
        for child in widget.winfo_children():
            cls = child.winfo_class()
            if cls in ("Frame",):
                child.config(bg=bg)
                self._apply_theme_to_children(child, bg, fg, btn_bg, btn_fg)
            elif cls == "Label":
                child.config(bg=bg, fg=fg)
            elif cls == "Checkbutton":
                child.config(bg=bg, fg=fg, selectcolor=bg, activebackground=bg)
            elif cls == "Button":
                child.config(bg=btn_bg, fg=btn_fg)

    # ------------------------------------------------------------------
    # Sound
    # ------------------------------------------------------------------

    def _play_sound(self, kind: str) -> None:
        """システムベルを使って音を鳴らす（プラットフォーム非依存）。"""
        try:
            if kind == "tick":
                # tick は短く鳴らす
                self.bell()
            else:
                self.bell()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    app = PomodoroApp()
    app.mainloop()


if __name__ == "__main__":
    main()

