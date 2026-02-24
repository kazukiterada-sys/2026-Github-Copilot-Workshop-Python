"""Tests for the Pomodoro Timer Flask app."""
import pytest
from app import app, POMODORO_DURATION, SHORT_BREAK_DURATION, LONG_BREAK_DURATION


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_returns_200(client):
    """Root route should return 200 and contain expected HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "ポモドーロタイマー" in response.data.decode("utf-8")


def test_settings_endpoint(client):
    """Settings API should return correct timer durations."""
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.get_json()
    assert data["pomodoro"] == POMODORO_DURATION
    assert data["shortBreak"] == SHORT_BREAK_DURATION
    assert data["longBreak"] == LONG_BREAK_DURATION


def test_pomodoro_duration_is_25_minutes():
    """Pomodoro session should be 25 minutes."""
    assert POMODORO_DURATION == 25 * 60


def test_short_break_duration_is_5_minutes():
    """Short break should be 5 minutes."""
    assert SHORT_BREAK_DURATION == 5 * 60


def test_long_break_duration_is_15_minutes():
    """Long break should be 15 minutes."""
    assert LONG_BREAK_DURATION == 15 * 60


def test_index_contains_circular_progress_canvas(client):
    """Index page should include the ring canvas for circular progress."""
    response = client.get("/")
    html = response.data.decode("utf-8")
    assert "ring-canvas" in html


def test_index_contains_background_canvas(client):
    """Index page should include the background canvas for particle effects."""
    response = client.get("/")
    html = response.data.decode("utf-8")
    assert "bg-canvas" in html


def test_index_contains_mode_tabs(client):
    """Index page should have the three mode tabs."""
    response = client.get("/")
    html = response.data.decode("utf-8")
    assert 'data-mode="pomodoro"' in html
    assert 'data-mode="shortBreak"' in html
    assert 'data-mode="longBreak"' in html


def test_index_contains_color_gradient_logic(client):
    """Index page should include colour gradient helper (blue/yellow/red)."""
    response = client.get("/")
    html = response.data.decode("utf-8")
    assert "progressColor" in html
    assert "lerpColor" in html
