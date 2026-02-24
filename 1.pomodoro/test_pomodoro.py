"""
ポモドーロタイマーのユニットテスト。

GUI に依存しない PomodoroSettings と PomodoroTimer クラスをテストします。
"""
import pytest

from timer import (
    BREAK_TIME_OPTIONS,
    THEMES,
    WORK_TIME_OPTIONS,
    PomodoroSettings,
    PomodoroTimer,
)


# ---------------------------------------------------------------------------
# PomodoroSettings のテスト
# ---------------------------------------------------------------------------


class TestPomodoroSettings:
    """PomodoroSettings の初期値・バリデーション・カスタマイズをテストする。"""

    def test_default_values(self):
        """デフォルト設定が正しい値であることを確認する。"""
        s = PomodoroSettings()
        assert s.work_minutes == 25
        assert s.break_minutes == 5
        assert s.theme == "ライト"
        assert s.sound_start is True
        assert s.sound_end is True
        assert s.sound_tick is False

    def test_valid_work_time_options(self):
        """有効な作業時間オプションがすべてバリデーションを通過する。"""
        for minutes in WORK_TIME_OPTIONS:
            s = PomodoroSettings(work_minutes=minutes)
            s.validate()  # 例外が発生しないこと

    def test_valid_break_time_options(self):
        """有効な休憩時間オプションがすべてバリデーションを通過する。"""
        for minutes in BREAK_TIME_OPTIONS:
            s = PomodoroSettings(break_minutes=minutes)
            s.validate()  # 例外が発生しないこと

    def test_valid_themes(self):
        """有効なテーマがすべてバリデーションを通過する。"""
        for theme in THEMES.keys():
            s = PomodoroSettings(theme=theme)
            s.validate()  # 例外が発生しないこと

    def test_invalid_work_minutes_raises(self):
        """無効な作業時間で ValueError が発生する。"""
        s = PomodoroSettings(work_minutes=99)
        with pytest.raises(ValueError, match="作業時間"):
            s.validate()

    def test_invalid_break_minutes_raises(self):
        """無効な休憩時間で ValueError が発生する。"""
        s = PomodoroSettings(break_minutes=99)
        with pytest.raises(ValueError, match="休憩時間"):
            s.validate()

    def test_invalid_theme_raises(self):
        """無効なテーマ名で ValueError が発生する。"""
        s = PomodoroSettings(theme="存在しないテーマ")
        with pytest.raises(ValueError, match="テーマ"):
            s.validate()

    def test_custom_settings(self):
        """作業時間 45 分・休憩 15 分・ダークテーマの設定が正しく保持される。"""
        s = PomodoroSettings(
            work_minutes=45,
            break_minutes=15,
            theme="ダーク",
            sound_start=False,
            sound_end=True,
            sound_tick=True,
        )
        s.validate()
        assert s.work_minutes == 45
        assert s.break_minutes == 15
        assert s.theme == "ダーク"
        assert s.sound_start is False
        assert s.sound_end is True
        assert s.sound_tick is True

    def test_focus_theme(self):
        """集中テーマが正しく設定できる。"""
        s = PomodoroSettings(theme="集中")
        s.validate()
        assert s.theme == "集中"

    def test_sound_all_off(self):
        """すべてのサウンドをオフに設定できる。"""
        s = PomodoroSettings(sound_start=False, sound_end=False, sound_tick=False)
        assert s.sound_start is False
        assert s.sound_end is False
        assert s.sound_tick is False


# ---------------------------------------------------------------------------
# PomodoroTimer のテスト
# ---------------------------------------------------------------------------


class TestPomodoroTimer:
    """PomodoroTimer のロジックをテストする。"""

    def _make_timer(self, work_minutes=25, break_minutes=5) -> PomodoroTimer:
        s = PomodoroSettings(work_minutes=work_minutes, break_minutes=break_minutes)
        return PomodoroTimer(s)

    def test_initial_state(self):
        """タイマーの初期状態が正しい。"""
        t = self._make_timer()
        assert t.phase == "work"
        assert t.remaining_seconds == 25 * 60
        assert t.running is False
        assert t.session_count == 0

    def test_display_time_initial(self):
        """初期状態の表示時間が MM:SS 形式で正しい。"""
        t = self._make_timer(work_minutes=25)
        assert t.display_time == "25:00"

    def test_display_time_15min(self):
        """15分設定の表示時間が正しい。"""
        t = self._make_timer(work_minutes=15)
        assert t.display_time == "15:00"

    def test_display_time_format(self):
        """残り時間がゼロ秒のとき 00:00 と表示される。"""
        t = self._make_timer()
        t.remaining_seconds = 0
        assert t.display_time == "00:00"

    def test_start(self):
        """start() を呼ぶと running が True になる。"""
        t = self._make_timer()
        t.start()
        assert t.running is True

    def test_pause(self):
        """pause() を呼ぶと running が False になる。"""
        t = self._make_timer()
        t.start()
        t.pause()
        assert t.running is False

    def test_tick_decrements_seconds(self):
        """tick() を呼ぶと残り時間が 1 秒減る。"""
        t = self._make_timer()
        t.start()
        initial = t.remaining_seconds
        t.tick()
        assert t.remaining_seconds == initial - 1

    def test_tick_returns_false_when_not_finished(self):
        """残り時間がある場合 tick() は False を返す。"""
        t = self._make_timer()
        t.start()
        result = t.tick()
        assert result is False

    def test_tick_returns_true_when_finished(self):
        """残り時間が 1 秒のとき tick() は True を返す。"""
        t = self._make_timer()
        t.remaining_seconds = 1
        t.start()
        result = t.tick()
        assert result is True
        assert t.remaining_seconds == 0

    def test_tick_does_nothing_when_paused(self):
        """停止中に tick() を呼んでも残り時間は変わらない。"""
        t = self._make_timer()
        initial = t.remaining_seconds
        t.tick()  # running=False なので何もしない
        assert t.remaining_seconds == initial

    def test_reset(self):
        """reset() でタイマーが初期状態に戻る。"""
        t = self._make_timer(work_minutes=35)
        t.start()
        for _ in range(10):
            t.tick()
        t.reset()
        assert t.remaining_seconds == 35 * 60
        assert t.running is False
        assert t.phase == "work"

    def test_next_phase_work_to_break(self):
        """next_phase() で作業→休憩フェーズに切り替わる。"""
        t = self._make_timer(break_minutes=10)
        t.next_phase()
        assert t.phase == "break"
        assert t.remaining_seconds == 10 * 60
        assert t.running is False

    def test_next_phase_break_to_work(self):
        """next_phase() で休憩→作業フェーズに切り替わり、セッション数が増える。"""
        t = self._make_timer(work_minutes=45)
        t.next_phase()  # work -> break
        t.next_phase()  # break -> work
        assert t.phase == "work"
        assert t.remaining_seconds == 45 * 60
        assert t.session_count == 1

    def test_session_count_increments(self):
        """複数セッションをこなすとセッション数が正しく増加する。"""
        t = self._make_timer()
        for _ in range(3):
            t.next_phase()  # work->break
            t.next_phase()  # break->work
        assert t.session_count == 3

    def test_phase_label_work(self):
        """作業フェーズのラベルが正しい。"""
        t = self._make_timer()
        assert "作業" in t.phase_label

    def test_phase_label_break(self):
        """休憩フェーズのラベルが正しい。"""
        t = self._make_timer()
        t.next_phase()
        assert "休憩" in t.phase_label

    def test_work_time_options_all_valid(self):
        """全作業時間オプションでタイマーが正しく初期化される。"""
        for minutes in WORK_TIME_OPTIONS:
            t = self._make_timer(work_minutes=minutes)
            assert t.remaining_seconds == minutes * 60

    def test_break_time_options_all_valid(self):
        """全休憩時間オプションでフェーズ切り替えが正しく動く。"""
        for minutes in BREAK_TIME_OPTIONS:
            t = self._make_timer(break_minutes=minutes)
            t.next_phase()
            assert t.remaining_seconds == minutes * 60


# ---------------------------------------------------------------------------
# テーマ定義のテスト
# ---------------------------------------------------------------------------


class TestThemes:
    """THEMES 定数の構造と内容をテストする。"""

    def test_required_themes_exist(self):
        """ライト・ダーク・集中テーマが定義されている。"""
        assert "ライト" in THEMES
        assert "ダーク" in THEMES
        assert "集中" in THEMES

    def test_theme_has_required_keys(self):
        """各テーマに必要なカラーキーが含まれている。"""
        required_keys = {"bg", "fg", "accent", "btn_bg", "btn_fg", "timer_fg"}
        for name, colors in THEMES.items():
            assert required_keys <= set(colors.keys()), (
                f"テーマ '{name}' に必要なキーが不足しています。"
            )

    def test_theme_values_are_color_strings(self):
        """各テーマの値が # で始まる色文字列である。"""
        for name, colors in THEMES.items():
            for key, value in colors.items():
                assert value.startswith("#"), (
                    f"テーマ '{name}' のキー '{key}' の値 '{value}' は有効な色コードではありません。"
                )
