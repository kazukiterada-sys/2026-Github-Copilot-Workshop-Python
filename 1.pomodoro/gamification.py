"""Gamification module for the Pomodoro Timer.

Handles XP, levels, badges, streaks, and session statistics.
User data is persisted in a JSON file.
"""

import json
import os
from datetime import date, timedelta
from typing import Any

DATA_FILE = os.path.join(os.path.dirname(__file__), "user_data.json")

XP_PER_SESSION = 25
LEVEL_XP_REQUIREMENT = 100

BADGE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "first_step",
        "name": "🏅 ファーストステップ",
        "description": "初めてのポモドーロを完了",
    },
    {
        "id": "hat_trick",
        "name": "🎯 ハットトリック",
        "description": "合計3回のポモドーロを完了",
    },
    {
        "id": "streak_3",
        "name": "🔥 3日連続",
        "description": "3日連続でポモドーロを完了",
    },
    {
        "id": "streak_7",
        "name": "⚡ 一週間継続",
        "description": "7日連続でポモドーロを完了",
    },
    {
        "id": "weekly_10",
        "name": "💪 週10回達成",
        "description": "1週間に10回以上のポモドーロを完了",
    },
    {
        "id": "marathon",
        "name": "🏆 マラソン",
        "description": "合計25回のポモドーロを完了",
    },
    {
        "id": "century",
        "name": "💯 センチュリー",
        "description": "合計100回のポモドーロを完了",
    },
]


def _default_data() -> dict[str, Any]:
    return {
        "xp": 0,
        "level": 1,
        "total_sessions": 0,
        "streak": 0,
        "last_session_date": None,
        "badges": [],
        "daily_sessions": {},
    }


def load_data() -> dict[str, Any]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        # Backfill any keys added after initial creation
        defaults = _default_data()
        for key, value in defaults.items():
            data.setdefault(key, value)
        return data
    return _default_data()


def save_data(data: dict[str, Any]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _sessions_this_week(data: dict[str, Any]) -> int:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    count = 0
    for date_str, sessions in data.get("daily_sessions", {}).items():
        try:
            d = date.fromisoformat(date_str)
        except ValueError:
            continue
        if monday <= d <= today:
            count += sessions
    return count


def _update_streak(data: dict[str, Any], today: date) -> None:
    last_str = data.get("last_session_date")
    if last_str is None:
        data["streak"] = 1
    else:
        last = date.fromisoformat(last_str)
        if last == today:
            pass  # Already counted today
        elif last == today - timedelta(days=1):
            data["streak"] += 1
        else:
            data["streak"] = 1
    data["last_session_date"] = today.isoformat()


def _check_badges(data: dict[str, Any]) -> list[str]:
    """Return list of newly earned badge names."""
    earned = data.get("badges", [])
    new_badges: list[str] = []
    total = data["total_sessions"]
    streak = data["streak"]
    weekly = _sessions_this_week(data)

    thresholds = {
        "first_step": total >= 1,
        "hat_trick": total >= 3,
        "streak_3": streak >= 3,
        "streak_7": streak >= 7,
        "weekly_10": weekly >= 10,
        "marathon": total >= 25,
        "century": total >= 100,
    }

    for badge in BADGE_DEFINITIONS:
        bid = badge["id"]
        if bid not in earned and thresholds.get(bid, False):
            earned.append(bid)
            new_badges.append(badge["name"])

    data["badges"] = earned
    return new_badges


def complete_session() -> dict[str, Any]:
    """Record a completed Pomodoro session.

    Returns a result dict with:
        xp_gained (int): XP added this session
        total_xp (int): Cumulative XP
        level (int): Current level
        level_up (bool): Whether a level-up occurred
        streak (int): Current streak
        new_badges (list[str]): Names of newly earned badges
        total_sessions (int): All-time completed sessions
        weekly_sessions (int): Sessions completed this week
    """
    data = load_data()
    today = date.today()
    today_str = today.isoformat()

    # XP & level
    data["xp"] += XP_PER_SESSION
    data["total_sessions"] += 1
    old_level = data["level"]
    data["level"] = (data["xp"] // LEVEL_XP_REQUIREMENT) + 1
    level_up = data["level"] > old_level

    # Daily count
    data["daily_sessions"][today_str] = data["daily_sessions"].get(today_str, 0) + 1

    # Streak
    _update_streak(data, today)

    # Badges
    new_badges = _check_badges(data)

    save_data(data)

    return {
        "xp_gained": XP_PER_SESSION,
        "total_xp": data["xp"],
        "level": data["level"],
        "level_up": level_up,
        "streak": data["streak"],
        "new_badges": new_badges,
        "total_sessions": data["total_sessions"],
        "weekly_sessions": _sessions_this_week(data),
    }


def get_stats() -> dict[str, Any]:
    """Return current gamification stats for display."""
    data = load_data()
    xp_in_level = data["xp"] % LEVEL_XP_REQUIREMENT
    badges_earned = [
        b for b in BADGE_DEFINITIONS if b["id"] in data.get("badges", [])
    ]
    badges_not_earned = [
        b for b in BADGE_DEFINITIONS if b["id"] not in data.get("badges", [])
    ]
    weekly = _sessions_this_week(data)

    # Last 7 days for mini chart
    today = date.today()
    daily_counts = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        daily_counts.append(data["daily_sessions"].get(d.isoformat(), 0))

    return {
        "level": data["level"],
        "xp": data["xp"],
        "xp_in_level": xp_in_level,
        "xp_to_next_level": LEVEL_XP_REQUIREMENT,
        "total_sessions": data["total_sessions"],
        "streak": data["streak"],
        "weekly_sessions": weekly,
        "badges_earned": badges_earned,
        "badges_not_earned": badges_not_earned,
        "daily_counts_7days": daily_counts,
    }
