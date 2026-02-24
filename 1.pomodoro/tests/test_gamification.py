"""Unit tests for gamification.py"""

import json
import os
import tempfile
from datetime import date, timedelta
from unittest import mock

import pytest

# Point DATA_FILE to a temp file for all tests
_tmp_dir_obj = tempfile.TemporaryDirectory()
_tmp_dir = _tmp_dir_obj.name
_test_data_file = os.path.join(_tmp_dir, "test_user_data.json")

import gamification

# Redirect the module's data file to the temp location
gamification.DATA_FILE = _test_data_file


def _reset():
    """Remove test data file between tests."""
    if os.path.exists(_test_data_file):
        os.remove(_test_data_file)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_state():
    _reset()
    yield
    _reset()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDefaultData:
    def test_default_data_keys(self):
        data = gamification._default_data()
        assert data["xp"] == 0
        assert data["level"] == 1
        assert data["total_sessions"] == 0
        assert data["streak"] == 0
        assert data["last_session_date"] is None
        assert data["badges"] == []
        assert data["daily_sessions"] == {}


class TestLoadSave:
    def test_load_creates_defaults(self):
        data = gamification.load_data()
        assert data["xp"] == 0

    def test_save_and_reload(self):
        data = gamification._default_data()
        data["xp"] = 75
        data["level"] = 2
        gamification.save_data(data)
        loaded = gamification.load_data()
        assert loaded["xp"] == 75
        assert loaded["level"] == 2

    def test_load_backfills_missing_keys(self):
        # Simulate old data file without 'daily_sessions'
        old_data = {"xp": 50, "level": 1, "total_sessions": 2, "streak": 1,
                    "last_session_date": None, "badges": []}
        with open(_test_data_file, "w", encoding="utf-8") as f:
            json.dump(old_data, f)
        data = gamification.load_data()
        assert "daily_sessions" in data


class TestXPAndLevels:
    def test_first_session_awards_xp(self):
        result = gamification.complete_session()
        assert result["xp_gained"] == gamification.XP_PER_SESSION
        assert result["total_xp"] == gamification.XP_PER_SESSION

    def test_level_up_occurs(self):
        # Fill XP to just below the threshold, then tip over
        data = gamification._default_data()
        data["xp"] = gamification.LEVEL_XP_REQUIREMENT - gamification.XP_PER_SESSION
        data["level"] = 1
        gamification.save_data(data)
        result = gamification.complete_session()
        assert result["level_up"] is True
        assert result["level"] == 2

    def test_no_level_up_below_threshold(self):
        result = gamification.complete_session()
        assert result["level_up"] is False
        assert result["level"] == 1

    def test_level_calculation(self):
        data = gamification._default_data()
        data["xp"] = 250  # level = 250 // 100 + 1 = 3
        data["level"] = 3
        gamification.save_data(data)
        stats = gamification.get_stats()
        assert stats["level"] == 3
        assert stats["xp_in_level"] == 50


class TestStreak:
    def test_first_session_streak_is_1(self):
        result = gamification.complete_session()
        assert result["streak"] == 1

    def test_consecutive_days_increment_streak(self):
        yesterday = date.today() - timedelta(days=1)
        data = gamification._default_data()
        data["streak"] = 2
        data["last_session_date"] = yesterday.isoformat()
        gamification.save_data(data)
        result = gamification.complete_session()
        assert result["streak"] == 3

    def test_gap_resets_streak(self):
        two_days_ago = date.today() - timedelta(days=2)
        data = gamification._default_data()
        data["streak"] = 5
        data["last_session_date"] = two_days_ago.isoformat()
        gamification.save_data(data)
        result = gamification.complete_session()
        assert result["streak"] == 1

    def test_same_day_does_not_increment_streak(self):
        today = date.today()
        data = gamification._default_data()
        data["streak"] = 3
        data["last_session_date"] = today.isoformat()
        gamification.save_data(data)
        result = gamification.complete_session()
        assert result["streak"] == 3


class TestBadges:
    def test_first_step_badge_on_first_session(self):
        result = gamification.complete_session()
        assert "🏅 ファーストステップ" in result["new_badges"]

    def test_hat_trick_badge_at_3_sessions(self):
        data = gamification._default_data()
        data["total_sessions"] = 2
        gamification.save_data(data)
        result = gamification.complete_session()
        assert "🎯 ハットトリック" in result["new_badges"]

    def test_streak_3_badge(self):
        yesterday = date.today() - timedelta(days=1)
        data = gamification._default_data()
        data["streak"] = 2
        data["last_session_date"] = yesterday.isoformat()
        data["badges"] = ["first_step"]
        gamification.save_data(data)
        result = gamification.complete_session()
        assert "🔥 3日連続" in result["new_badges"]

    def test_badge_not_earned_twice(self):
        data = gamification._default_data()
        data["badges"] = ["first_step"]
        data["total_sessions"] = 1
        gamification.save_data(data)
        result = gamification.complete_session()
        badge_names = result["new_badges"]
        assert badge_names.count("🏅 ファーストステップ") == 0

    def test_marathon_badge_at_25_sessions(self):
        data = gamification._default_data()
        data["total_sessions"] = 24
        data["badges"] = ["first_step", "hat_trick"]
        gamification.save_data(data)
        result = gamification.complete_session()
        assert "🏆 マラソン" in result["new_badges"]


class TestWeeklySessions:
    def test_sessions_this_week(self):
        today = date.today()
        data = gamification._default_data()
        data["daily_sessions"][today.isoformat()] = 3
        gamification.save_data(data)
        assert gamification._sessions_this_week(data) == 3

    def test_weekly_10_badge(self):
        today = date.today()
        data = gamification._default_data()
        # 9 sessions already this week
        data["daily_sessions"][today.isoformat()] = 9
        data["total_sessions"] = 9
        data["badges"] = ["first_step", "hat_trick"]
        gamification.save_data(data)
        result = gamification.complete_session()
        assert "💪 週10回達成" in result["new_badges"]


class TestGetStats:
    def test_get_stats_returns_expected_keys(self):
        stats = gamification.get_stats()
        for key in ("level", "xp", "xp_in_level", "xp_to_next_level",
                    "total_sessions", "streak", "weekly_sessions",
                    "badges_earned", "badges_not_earned", "daily_counts_7days"):
            assert key in stats, f"Missing key: {key}"

    def test_daily_counts_7days_length(self):
        stats = gamification.get_stats()
        assert len(stats["daily_counts_7days"]) == 7

    def test_stats_reflect_completed_session(self):
        gamification.complete_session()
        stats = gamification.get_stats()
        assert stats["total_sessions"] == 1
        assert stats["xp"] == gamification.XP_PER_SESSION
