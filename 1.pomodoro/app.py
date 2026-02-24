"""ポモドーロタイマー Flask アプリケーション"""
import os
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    """トップページ（タイマー UI）を返す。"""
    return render_template("index.html")


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
