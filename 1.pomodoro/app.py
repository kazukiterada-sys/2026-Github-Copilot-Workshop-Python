"""Pomodoro Timer with Gamification Elements.

Features:
- 25-minute work / 5-minute break cycles
- XP system: earn XP per completed Pomodoro, level up at each 100 XP
- Achievement badges: 初めての完了, ハットトリック, 3日連続, 一週間継続, 週10回, マラソン, センチュリー
- Streak display: consecutive days counter
- Statistics window: 7-day bar chart, total sessions, weekly count, all badges
"""

import tkinter as tk
from tkinter import ttk, messagebox
import gamification


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WORK_MINUTES = 25
BREAK_MINUTES = 5

COLOR_BG = "#1e1e2e"
COLOR_FG = "#cdd6f4"
COLOR_ACCENT = "#89b4fa"
COLOR_SUCCESS = "#a6e3a1"
COLOR_WARNING = "#f9e2af"
COLOR_DANGER = "#f38ba8"
COLOR_SURFACE = "#313244"
COLOR_XP_BAR_BG = "#45475a"
COLOR_XP_BAR_FG = "#89b4fa"
COLOR_STREAK = "#fab387"


# ---------------------------------------------------------------------------
# Stats Window
# ---------------------------------------------------------------------------

def open_stats_window(parent: tk.Tk) -> None:
    """Open a separate window showing detailed gamification statistics."""
    stats = gamification.get_stats()

    win = tk.Toplevel(parent)
    win.title("📊 統計・バッジ")
    win.configure(bg=COLOR_BG)
    win.resizable(False, False)

    pad = {"padx": 16, "pady": 6}

    # --- Title ---
    tk.Label(win, text="📊 統計・バッジ", font=("Helvetica", 16, "bold"),
             bg=COLOR_BG, fg=COLOR_FG).pack(**pad)

    # --- Summary row ---
    summary_frame = tk.Frame(win, bg=COLOR_SURFACE, bd=0)
    summary_frame.pack(fill="x", padx=16, pady=6)

    for label, value in [
        ("🎮 レベル", f"Lv.{stats['level']}"),
        ("⭐ 累計XP", f"{stats['xp']} XP"),
        ("📅 累計回数", f"{stats['total_sessions']} 回"),
        ("🔥 ストリーク", f"{stats['streak']} 日"),
        ("⚡ 今週", f"{stats['weekly_sessions']} 回"),
    ]:
        col = tk.Frame(summary_frame, bg=COLOR_SURFACE)
        col.pack(side="left", expand=True, fill="x", padx=8, pady=8)
        tk.Label(col, text=label, font=("Helvetica", 9), bg=COLOR_SURFACE,
                 fg=COLOR_ACCENT).pack()
        tk.Label(col, text=value, font=("Helvetica", 13, "bold"),
                 bg=COLOR_SURFACE, fg=COLOR_FG).pack()

    # --- 7-day chart ---
    tk.Label(win, text="📅 直近7日間の完了数", font=("Helvetica", 11, "bold"),
             bg=COLOR_BG, fg=COLOR_FG).pack(**pad)

    chart_frame = tk.Frame(win, bg=COLOR_BG)
    chart_frame.pack(padx=16, pady=4)

    counts = stats["daily_counts_7days"]
    max_count = max(counts) if any(counts) else 1
    bar_max_height = 80

    from datetime import date, timedelta
    today = date.today()
    for i, count in enumerate(counts):
        d = today - timedelta(days=6 - i)
        bar_height = max(4, int(bar_max_height * count / max_count)) if count else 4
        col_frame = tk.Frame(chart_frame, bg=COLOR_BG)
        col_frame.grid(row=0, column=i, padx=3)

        # count label
        tk.Label(col_frame, text=str(count) if count else "",
                 font=("Helvetica", 8), bg=COLOR_BG, fg=COLOR_FG).pack()

        # bar canvas
        canvas = tk.Canvas(col_frame, width=28, height=bar_max_height,
                            bg=COLOR_BG, highlightthickness=0)
        canvas.pack()
        y0 = bar_max_height - bar_height
        fill = COLOR_ACCENT if count else COLOR_SURFACE
        canvas.create_rectangle(2, y0, 26, bar_max_height, fill=fill, outline="")

        # day label
        day_str = d.strftime("%m/%d")
        tk.Label(col_frame, text=day_str, font=("Helvetica", 7),
                 bg=COLOR_BG, fg=COLOR_FG).pack()

    # --- Badges ---
    tk.Label(win, text="🏅 獲得バッジ", font=("Helvetica", 11, "bold"),
             bg=COLOR_BG, fg=COLOR_FG).pack(**pad)

    badge_frame = tk.Frame(win, bg=COLOR_BG)
    badge_frame.pack(padx=16, pady=4, fill="x")

    earned_ids = {b["id"] for b in stats["badges_earned"]}
    for badge in gamification.BADGE_DEFINITIONS:
        earned = badge["id"] in earned_ids
        row = tk.Frame(badge_frame, bg=COLOR_SURFACE if earned else COLOR_BG)
        row.pack(fill="x", pady=2, padx=2)
        fg = COLOR_SUCCESS if earned else "#6c7086"
        status = "✅" if earned else "🔒"
        tk.Label(row, text=f"{status} {badge['name']}", font=("Helvetica", 10, "bold"),
                 bg=row["bg"], fg=fg, width=24, anchor="w").pack(side="left", padx=6, pady=3)
        tk.Label(row, text=badge["description"], font=("Helvetica", 9),
                 bg=row["bg"], fg=fg, anchor="w").pack(side="left", padx=4)

    tk.Button(win, text="閉じる", command=win.destroy,
              bg=COLOR_SURFACE, fg=COLOR_FG, relief="flat",
              font=("Helvetica", 10), padx=12, pady=4).pack(pady=12)


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class PomodoroApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("🍅 Pomodoro Timer")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self._is_work = True   # True = work phase, False = break phase
        self._running = False
        self._after_id: str | None = None
        self._remaining = WORK_MINUTES * 60  # seconds

        self._build_ui()
        self._refresh_stats()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = self.root

        # ---- Top gamification bar ----
        top = tk.Frame(root, bg=COLOR_SURFACE)
        top.pack(fill="x", padx=0, pady=0)

        # Level
        self._lv_label = tk.Label(top, text="Lv.1", font=("Helvetica", 11, "bold"),
                                  bg=COLOR_SURFACE, fg=COLOR_ACCENT)
        self._lv_label.pack(side="left", padx=(12, 4), pady=6)

        # XP bar container
        xp_frame = tk.Frame(top, bg=COLOR_SURFACE)
        xp_frame.pack(side="left", expand=True, fill="x", padx=4, pady=6)

        self._xp_label = tk.Label(xp_frame, text="0 / 100 XP",
                                  font=("Helvetica", 8), bg=COLOR_SURFACE, fg=COLOR_FG)
        self._xp_label.pack(anchor="w")

        self._xp_bar_bg = tk.Canvas(xp_frame, height=8, bg=COLOR_XP_BAR_BG,
                                    highlightthickness=0)
        self._xp_bar_bg.pack(fill="x")
        self._xp_bar_rect = self._xp_bar_bg.create_rectangle(
            0, 0, 0, 8, fill=COLOR_XP_BAR_FG, outline=""
        )

        # Streak
        self._streak_label = tk.Label(top, text="🔥 0日", font=("Helvetica", 10, "bold"),
                                      bg=COLOR_SURFACE, fg=COLOR_STREAK)
        self._streak_label.pack(side="right", padx=(4, 12), pady=6)

        # Stats button
        tk.Button(top, text="📊", command=self._show_stats,
                  bg=COLOR_SURFACE, fg=COLOR_FG, relief="flat",
                  font=("Helvetica", 12), bd=0, padx=4).pack(side="right", pady=6)

        # ---- Phase label ----
        self._phase_label = tk.Label(root, text="🍅 作業タイム",
                                     font=("Helvetica", 14, "bold"),
                                     bg=COLOR_BG, fg=COLOR_FG)
        self._phase_label.pack(pady=(18, 4))

        # ---- Timer display ----
        self._timer_label = tk.Label(root, text="25:00",
                                     font=("Helvetica", 72, "bold"),
                                     bg=COLOR_BG, fg=COLOR_FG)
        self._timer_label.pack(pady=4)

        # ---- Session count ----
        self._session_label = tk.Label(root, text="完了: 0 回",
                                       font=("Helvetica", 10),
                                       bg=COLOR_BG, fg=COLOR_ACCENT)
        self._session_label.pack(pady=2)

        # ---- Buttons ----
        btn_frame = tk.Frame(root, bg=COLOR_BG)
        btn_frame.pack(pady=12)

        self._start_btn = tk.Button(
            btn_frame, text="▶ スタート", command=self._toggle,
            font=("Helvetica", 13, "bold"),
            bg=COLOR_ACCENT, fg=COLOR_BG, relief="flat",
            padx=18, pady=8
        )
        self._start_btn.pack(side="left", padx=6)

        tk.Button(
            btn_frame, text="↺ リセット", command=self._reset,
            font=("Helvetica", 11),
            bg=COLOR_SURFACE, fg=COLOR_FG, relief="flat",
            padx=12, pady=8
        ).pack(side="left", padx=6)

        # ---- Notification area ----
        self._notify_label = tk.Label(root, text="",
                                      font=("Helvetica", 10, "italic"),
                                      bg=COLOR_BG, fg=COLOR_SUCCESS, wraplength=340)
        self._notify_label.pack(pady=(0, 12))

    # ------------------------------------------------------------------
    # Timer Logic
    # ------------------------------------------------------------------

    def _toggle(self) -> None:
        if self._running:
            self._pause()
        else:
            self._start()

    def _start(self) -> None:
        self._running = True
        self._start_btn.config(text="⏸ 一時停止")
        self._tick()

    def _pause(self) -> None:
        self._running = False
        self._start_btn.config(text="▶ 再開")
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def _reset(self) -> None:
        self._pause()
        self._is_work = True
        self._remaining = WORK_MINUTES * 60
        self._phase_label.config(text="🍅 作業タイム", fg=COLOR_FG)
        self._timer_label.config(fg=COLOR_FG)
        self._start_btn.config(text="▶ スタート")
        self._update_clock()
        self._notify_label.config(text="")

    def _tick(self) -> None:
        if not self._running:
            return
        if self._remaining <= 0:
            self._phase_complete()
            return
        self._remaining -= 1
        self._update_clock()
        # Warn in last 60s of work phase
        if self._is_work and self._remaining <= 60:
            self._timer_label.config(fg=COLOR_WARNING)
        self._after_id = self.root.after(1000, self._tick)

    def _update_clock(self) -> None:
        mins, secs = divmod(self._remaining, 60)
        self._timer_label.config(text=f"{mins:02d}:{secs:02d}")

    def _phase_complete(self) -> None:
        self._running = False
        self._after_id = None

        if self._is_work:
            # Record session & update gamification
            result = gamification.complete_session()
            self._on_session_complete(result)
            # Switch to break
            self._is_work = False
            self._remaining = BREAK_MINUTES * 60
            self._phase_label.config(text="☕ 休憩タイム", fg=COLOR_SUCCESS)
            self._timer_label.config(fg=COLOR_SUCCESS)
            self._start_btn.config(text="▶ 休憩スタート")
        else:
            # Break done → back to work
            self._is_work = True
            self._remaining = WORK_MINUTES * 60
            self._phase_label.config(text="🍅 作業タイム", fg=COLOR_FG)
            self._timer_label.config(fg=COLOR_FG)
            self._start_btn.config(text="▶ スタート")
            self._notify_label.config(text="休憩終了！次のポモドーロを始めましょう 💪")
            self._update_clock()

    def _on_session_complete(self, result: dict) -> None:
        self._refresh_stats()

        msgs = [f"✅ ポモドーロ完了！ +{result['xp_gained']} XP"]
        if result["level_up"]:
            msgs.append(f"🎉 レベルアップ！ → Lv.{result['level']}")
        if result["new_badges"]:
            badges_str = " ".join(result["new_badges"])
            msgs.append(f"🏅 新バッジ獲得: {badges_str}")
        self._notify_label.config(text=" | ".join(msgs))
        self._update_clock()

    # ------------------------------------------------------------------
    # Gamification UI refresh
    # ------------------------------------------------------------------

    def _refresh_stats(self) -> None:
        stats = gamification.get_stats()

        self._lv_label.config(text=f"Lv.{stats['level']}")
        xp_in = stats["xp_in_level"]
        xp_max = stats["xp_to_next_level"]
        self._xp_label.config(text=f"{xp_in} / {xp_max} XP")

        # Update XP bar width
        self._xp_bar_bg.update_idletasks()
        width = self._xp_bar_bg.winfo_width()
        fill_w = int(width * xp_in / xp_max) if xp_max else 0
        self._xp_bar_bg.coords(self._xp_bar_rect, 0, 0, fill_w, 8)

        self._streak_label.config(text=f"🔥 {stats['streak']}日")
        self._session_label.config(text=f"完了: {stats['total_sessions']} 回  /  今週: {stats['weekly_sessions']} 回")

    def _show_stats(self) -> None:
        open_stats_window(self.root)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
