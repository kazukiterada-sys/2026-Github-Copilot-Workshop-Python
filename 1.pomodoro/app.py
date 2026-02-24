"""Pomodoro Timer Flask Application."""

from flask import Flask, jsonify, render_template
from timer import PomodoroTimer

app = Flask(__name__)
timer = PomodoroTimer()


@app.route("/")
def index():
    """Render the main timer page."""
    return render_template("index.html")


@app.route("/api/status")
def status():
    """Return the current timer status."""
    return jsonify(timer.status())


@app.route("/api/start", methods=["POST"])
def start():
    """Start or resume the timer."""
    timer.start()
    return jsonify(timer.status())


@app.route("/api/stop", methods=["POST"])
def stop():
    """Stop (pause) the timer."""
    timer.stop()
    return jsonify(timer.status())


@app.route("/api/reset", methods=["POST"])
def reset():
    """Reset the timer to initial state."""
    timer.stop()
    timer.reset()
    return jsonify(timer.status())


if __name__ == "__main__":
    app.run()
