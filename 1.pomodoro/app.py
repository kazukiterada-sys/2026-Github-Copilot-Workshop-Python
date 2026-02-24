# Pomodoro Timer App
from flask import Flask, jsonify, render_template
from timer import PomodoroTimer

app = Flask(__name__)
timer = PomodoroTimer()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start():
    timer.start()
    return jsonify(timer.get_status())


@app.route('/api/stop', methods=['POST'])
def stop():
    timer.stop()
    return jsonify(timer.get_status())


@app.route('/api/reset', methods=['POST'])
def reset():
    timer.reset()
    return jsonify(timer.get_status())


@app.route('/api/status', methods=['GET'])
def status():
    return jsonify(timer.get_status())


if __name__ == '__main__':
    app.run()
