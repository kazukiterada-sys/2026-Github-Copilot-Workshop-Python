# ポモドーロタイマーアプリ - メインアプリケーション

import os
from datetime import datetime, timezone

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
    jsonify,
    flash,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================
# アプリケーションの初期化
# ============================================================

def create_app(test_config=None):
    """アプリケーションファクトリ関数"""
    app = Flask(__name__)

    # 基本設定
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    if test_config is not None:
        # テスト用の設定を適用
        app.config.update(test_config)
    else:
        # 本番用のSQLiteデータベースパス
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(basedir, 'pomodoro.db')}",
        )

    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # データベースとログインマネージャーの初期化
    db.init_app(app)
    login_manager.init_app(app)

    # ルートの登録
    _register_routes(app, db)

    # アプリケーション起動時にテーブルを作成
    with app.app_context():
        db.create_all()

    return app


# ============================================================
# 拡張機能のインスタンス（アプリ外で初期化）
# ============================================================

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"  # 未ログイン時のリダイレクト先
login_manager.login_message = "このページにアクセスするにはログインが必要です。"


# ============================================================
# データベースモデル
# ============================================================

class User(UserMixin, db.Model):
    """ユーザーモデル"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # タイマー設定（ユーザーごとにカスタマイズ可能）
    work_duration = db.Column(db.Integer, default=25, nullable=False)          # 作業時間（分）
    short_break = db.Column(db.Integer, default=5, nullable=False)             # 短い休憩（分）
    long_break = db.Column(db.Integer, default=15, nullable=False)             # 長い休憩（分）
    sessions_before_long_break = db.Column(db.Integer, default=4, nullable=False)  # 長い休憩までのセッション数

    # リレーション
    sessions = db.relationship("PomodoroSession", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """パスワードをハッシュ化して保存"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """パスワードを検証"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class PomodoroSession(db.Model):
    """ポモドーロセッションモデル"""
    __tablename__ = "pomodoro_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_type = db.Column(db.String(10), nullable=False)      # 'work' または 'break'
    duration_minutes = db.Column(db.Integer, nullable=False)     # セッションの長さ（分）
    completed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PomodoroSession {self.session_type} {self.duration_minutes}min>"


# ============================================================
# ルート定義
# ============================================================

def _register_routes(app, db):
    """アプリケーションのルートを登録"""

    @login_manager.user_loader
    def load_user(user_id):
        """ユーザーIDからユーザーオブジェクトを取得"""
        return db.session.get(User, int(user_id))

    # ----------------------------------------
    # トップページ
    # ----------------------------------------
    @app.route("/")
    def index():
        """トップページ：ログイン済みならタイマーへ、未ログインならログインページへ"""
        if current_user.is_authenticated:
            return redirect(url_for("timer"))
        return redirect(url_for("login"))

    # ----------------------------------------
    # ユーザー登録
    # ----------------------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        """ユーザー登録ページ"""
        if current_user.is_authenticated:
            return redirect(url_for("timer"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            # バリデーション
            if not username or not password:
                flash("ユーザー名とパスワードを入力してください。", "danger")
                return render_template("register.html")

            if password != confirm:
                flash("パスワードが一致しません。", "danger")
                return render_template("register.html")

            if len(password) < 4:
                flash("パスワードは4文字以上で入力してください。", "danger")
                return render_template("register.html")

            # 重複チェック
            existing = User.query.filter_by(username=username).first()
            if existing:
                flash("このユーザー名は既に使用されています。", "danger")
                return render_template("register.html")

            # ユーザー作成
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash("アカウントが作成されました。ログインしてください。", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    # ----------------------------------------
    # ログイン
    # ----------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """ログインページ"""
        if current_user.is_authenticated:
            return redirect(url_for("timer"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash("ログインしました。", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("timer"))
            else:
                flash("ユーザー名またはパスワードが正しくありません。", "danger")

        return render_template("login.html")

    # ----------------------------------------
    # ログアウト
    # ----------------------------------------
    @app.route("/logout")
    @login_required
    def logout():
        """ログアウト"""
        logout_user()
        flash("ログアウトしました。", "info")
        return redirect(url_for("login"))

    # ----------------------------------------
    # タイマーページ
    # ----------------------------------------
    @app.route("/timer")
    @login_required
    def timer():
        """メインのポモドーロタイマーページ"""
        return render_template("index.html", user=current_user)

    # ----------------------------------------
    # 設定ページ
    # ----------------------------------------
    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    def settings():
        """タイマー設定ページ"""
        if request.method == "POST":
            try:
                work = int(request.form.get("work_duration", 25))
                short = int(request.form.get("short_break", 5))
                long = int(request.form.get("long_break", 15))
                sessions = int(request.form.get("sessions_before_long_break", 4))
            except (ValueError, TypeError):
                flash("入力値が正しくありません。数値を入力してください。", "danger")
                return render_template("settings.html", user=current_user)

            # 値の範囲チェック
            if not (1 <= work <= 120):
                flash("作業時間は1〜120分の範囲で入力してください。", "danger")
                return render_template("settings.html", user=current_user)
            if not (1 <= short <= 60):
                flash("短い休憩は1〜60分の範囲で入力してください。", "danger")
                return render_template("settings.html", user=current_user)
            if not (1 <= long <= 60):
                flash("長い休憩は1〜60分の範囲で入力してください。", "danger")
                return render_template("settings.html", user=current_user)
            if not (1 <= sessions <= 10):
                flash("長い休憩までのセッション数は1〜10の範囲で入力してください。", "danger")
                return render_template("settings.html", user=current_user)

            # 設定を保存
            current_user.work_duration = work
            current_user.short_break = short
            current_user.long_break = long
            current_user.sessions_before_long_break = sessions
            db.session.commit()

            flash("設定を保存しました。", "success")
            return redirect(url_for("timer"))

        return render_template("settings.html", user=current_user)

    # ----------------------------------------
    # 履歴ページ
    # ----------------------------------------
    @app.route("/history")
    @login_required
    def history():
        """セッション履歴と統計ページ"""
        # 最新50件のセッションを取得
        sessions = (
            PomodoroSession.query
            .filter_by(user_id=current_user.id)
            .order_by(PomodoroSession.completed_at.desc())
            .limit(50)
            .all()
        )

        # 統計情報の計算
        all_sessions = PomodoroSession.query.filter_by(user_id=current_user.id).all()
        total_sessions = len(all_sessions)
        work_sessions = [s for s in all_sessions if s.session_type == "work"]
        total_work_sessions = len(work_sessions)
        total_work_minutes = sum(s.duration_minutes for s in work_sessions)

        return render_template(
            "history.html",
            sessions=sessions,
            total_sessions=total_sessions,
            total_work_sessions=total_work_sessions,
            total_work_minutes=total_work_minutes,
        )

    # ----------------------------------------
    # API: セッション記録
    # ----------------------------------------
    @app.route("/api/session", methods=["POST"])
    @login_required
    def record_session():
        """完了したポモドーロセッションを記録するAPI"""
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "JSONデータが必要です"}), 400

        session_type = data.get("session_type")
        duration_minutes = data.get("duration_minutes")

        # バリデーション
        if session_type not in ("work", "break"):
            return jsonify({"error": "session_type は 'work' または 'break' を指定してください"}), 400

        if not isinstance(duration_minutes, int) or duration_minutes <= 0:
            return jsonify({"error": "duration_minutes は正の整数を指定してください"}), 400

        # セッションを保存
        session = PomodoroSession(
            user_id=current_user.id,
            session_type=session_type,
            duration_minutes=duration_minutes,
            completed_at=datetime.now(timezone.utc),
        )
        db.session.add(session)
        db.session.commit()

        return jsonify({"message": "セッションを記録しました", "id": session.id}), 201


# ============================================================
# アプリケーションのエントリーポイント
# ============================================================

app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)
