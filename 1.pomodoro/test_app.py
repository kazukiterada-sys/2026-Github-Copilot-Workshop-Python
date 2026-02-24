"""ポモドーロタイマー APIの単体テスト"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

import app as pomodoro_app
import pytest


@pytest.fixture(autouse=True)
def reset_state():
    """各テスト前後にタイマー状態をリセットする"""
    with pomodoro_app.timer_lock:
        pomodoro_app.timer_state["mode"] = "work"
        pomodoro_app.timer_state["remaining"] = 25 * 60
        pomodoro_app.timer_state["running"] = False
    yield
    with pomodoro_app.timer_lock:
        pomodoro_app.timer_state["running"] = False


@pytest.fixture
def client():
    pomodoro_app.app.config["TESTING"] = True
    with pomodoro_app.app.test_client() as c:
        yield c


# ── GET /api/status ──────────────────────────────────────

def test_status_initial(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.get_json()
    assert data["mode"] == "work"
    assert data["remaining"] == 25 * 60
    assert data["running"] is False


# ── POST /api/start ──────────────────────────────────────

def test_start(client):
    res = client.post("/api/start")
    assert res.status_code == 200
    data = res.get_json()
    assert data["running"] is True
    assert data["message"] == "started"


def test_start_already_running(client):
    client.post("/api/start")
    res = client.post("/api/start")
    assert res.status_code == 200
    data = res.get_json()
    assert data["message"] == "already running"


# ── POST /api/stop ───────────────────────────────────────

def test_stop(client):
    client.post("/api/start")
    res = client.post("/api/stop")
    assert res.status_code == 200
    data = res.get_json()
    assert data["running"] is False
    assert data["message"] == "stopped"


# ── POST /api/reset ──────────────────────────────────────

def test_reset(client):
    client.post("/api/start")
    time.sleep(0.1)
    client.post("/api/stop")
    res = client.post("/api/reset")
    assert res.status_code == 200
    data = res.get_json()
    assert data["running"] is False
    assert data["mode"] == "work"
    assert data["remaining"] == 25 * 60
    assert data["message"] == "reset"


# ── GET / (HTML) ─────────────────────────────────────────

def test_index_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"<!DOCTYPE html>" in res.data
