# Pomodoro Timer App
import time
import threading
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# タイマー状態管理（インメモリ）
timer_state = {
    "mode": "work",           # "work" or "break"
    "remaining": 25 * 60,     # 残り秒数（初期値：作業25分）
    "running": False,
    "work_duration": 25 * 60,
    "break_duration": 5 * 60,
}
timer_lock = threading.Lock()
timer_thread = None


def _tick():
    """バックグラウンドでタイマーをカウントダウンするスレッド"""
    while True:
        time.sleep(1)
        with timer_lock:
            if not timer_state["running"]:
                break
            if timer_state["remaining"] > 0:
                timer_state["remaining"] -= 1
            else:
                # 作業↔休憩を切り替え、停止
                if timer_state["mode"] == "work":
                    timer_state["mode"] = "break"
                    timer_state["remaining"] = timer_state["break_duration"]
                else:
                    timer_state["mode"] = "work"
                    timer_state["remaining"] = timer_state["work_duration"]
                timer_state["running"] = False
                break


# ─────────────────────── ページ ───────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────── REST API ───────────────────────

@app.route("/api/status", methods=["GET"])
def api_status():
    with timer_lock:
        return jsonify({
            "mode": timer_state["mode"],
            "remaining": timer_state["remaining"],
            "running": timer_state["running"],
        })


@app.route("/api/start", methods=["POST"])
def api_start():
    global timer_thread
    with timer_lock:
        if timer_state["running"]:
            return jsonify({
                "message": "already running",
                "mode": timer_state["mode"],
                "remaining": timer_state["remaining"],
                "running": timer_state["running"],
            }), 200
        timer_state["running"] = True
        mode = timer_state["mode"]
        remaining = timer_state["remaining"]

    timer_thread = threading.Thread(target=_tick, daemon=True)
    timer_thread.start()

    return jsonify({
        "message": "started",
        "mode": mode,
        "remaining": remaining,
        "running": True,
    })


@app.route("/api/stop", methods=["POST"])
def api_stop():
    with timer_lock:
        timer_state["running"] = False
        return jsonify({
            "message": "stopped",
            "mode": timer_state["mode"],
            "remaining": timer_state["remaining"],
            "running": timer_state["running"],
        })


@app.route("/api/reset", methods=["POST"])
def api_reset():
    with timer_lock:
        timer_state["running"] = False
        timer_state["mode"] = "work"
        timer_state["remaining"] = timer_state["work_duration"]
        return jsonify({
            "message": "reset",
            "mode": timer_state["mode"],
            "remaining": timer_state["remaining"],
            "running": timer_state["running"],
        })


if __name__ == "__main__":
    app.run(debug=False)
