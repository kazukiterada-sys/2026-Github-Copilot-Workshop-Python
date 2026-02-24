"""Pomodoro Timer App - Enhanced Visual Feedback"""
from flask import Flask, render_template, jsonify

app = Flask(__name__)

POMODORO_DURATION = 25 * 60  # seconds
SHORT_BREAK_DURATION = 5 * 60
LONG_BREAK_DURATION = 15 * 60


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/settings")
def get_settings():
    return jsonify(
        {
            "pomodoro": POMODORO_DURATION,
            "shortBreak": SHORT_BREAK_DURATION,
            "longBreak": LONG_BREAK_DURATION,
        }
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)
