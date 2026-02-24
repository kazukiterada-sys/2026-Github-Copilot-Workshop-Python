# ポモドーロタイマーアプリのテスト

import pytest
import sys
import os

# テスト対象モジュールのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app, db, User, PomodoroSession


# ============================================================
# テスト用フィクスチャ
# ============================================================

@pytest.fixture
def app():
    """テスト用アプリケーションを作成する（インメモリSQLite使用）"""
    test_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
    })

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()


@pytest.fixture
def client(app):
    """テスト用HTTPクライアント"""
    return app.test_client()


@pytest.fixture
def registered_user(app, client):
    """登録済みユーザーを作成するフィクスチャ"""
    client.post("/register", data={
        "username": "testuser",
        "password": "testpass",
        "confirm_password": "testpass",
    })
    return {"username": "testuser", "password": "testpass"}


@pytest.fixture
def logged_in_client(app, client, registered_user):
    """ログイン済みクライアントを返すフィクスチャ"""
    client.post("/login", data={
        "username": registered_user["username"],
        "password": registered_user["password"],
    })
    return client


# ============================================================
# ユーザー登録のテスト
# ============================================================

class TestRegister:
    """ユーザー登録のテスト"""

    def test_register_page_loads(self, client):
        """登録ページが正常に表示される"""
        response = client.get("/register")
        assert response.status_code == 200
        assert "登録" in response.data.decode("utf-8")

    def test_register_success(self, app, client):
        """正常なユーザー登録"""
        response = client.post("/register", data={
            "username": "newuser",
            "password": "password123",
            "confirm_password": "password123",
        }, follow_redirects=True)
        assert response.status_code == 200

        # データベースにユーザーが作成されている
        with app.app_context():
            user = User.query.filter_by(username="newuser").first()
            assert user is not None
            assert user.username == "newuser"
            # パスワードがハッシュ化されている（平文ではない）
            assert user.password_hash != "password123"

    def test_register_duplicate_username(self, client, registered_user):
        """同じユーザー名での重複登録はエラー"""
        response = client.post("/register", data={
            "username": "testuser",
            "password": "anotherpass",
            "confirm_password": "anotherpass",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "既に使用されています" in response.data.decode("utf-8")

    def test_register_password_mismatch(self, client):
        """パスワード不一致の場合はエラー"""
        response = client.post("/register", data={
            "username": "user2",
            "password": "pass1",
            "confirm_password": "pass2",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "一致しません" in response.data.decode("utf-8")

    def test_register_short_password(self, client):
        """短すぎるパスワードはエラー"""
        response = client.post("/register", data={
            "username": "user3",
            "password": "abc",
            "confirm_password": "abc",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "4文字以上" in response.data.decode("utf-8")

    def test_register_default_settings(self, app, client):
        """登録ユーザーのデフォルト設定が正しい"""
        client.post("/register", data={
            "username": "settingsuser",
            "password": "pass1234",
            "confirm_password": "pass1234",
        })
        with app.app_context():
            user = User.query.filter_by(username="settingsuser").first()
            assert user.work_duration == 25
            assert user.short_break == 5
            assert user.long_break == 15
            assert user.sessions_before_long_break == 4


# ============================================================
# ログイン・ログアウトのテスト
# ============================================================

class TestLoginLogout:
    """ログイン・ログアウトのテスト"""

    def test_login_page_loads(self, client):
        """ログインページが正常に表示される"""
        response = client.get("/login")
        assert response.status_code == 200
        assert "ログイン" in response.data.decode("utf-8")

    def test_login_success(self, client, registered_user):
        """正常なログイン"""
        response = client.post("/login", data={
            "username": registered_user["username"],
            "password": registered_user["password"],
        }, follow_redirects=True)
        assert response.status_code == 200
        # ログイン後はタイマーページへリダイレクト
        assert "タイマー" in response.data.decode("utf-8") or "timer" in response.request.path.lower()

    def test_login_wrong_password(self, client, registered_user):
        """誤ったパスワードでのログインは失敗"""
        response = client.post("/login", data={
            "username": registered_user["username"],
            "password": "wrongpassword",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "正しくありません" in response.data.decode("utf-8")

    def test_login_wrong_username(self, client):
        """存在しないユーザー名でのログインは失敗"""
        response = client.post("/login", data={
            "username": "nonexistent",
            "password": "somepassword",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "正しくありません" in response.data.decode("utf-8")

    def test_logout(self, logged_in_client):
        """ログアウトが正常に機能する"""
        response = logged_in_client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert "ログアウト" in response.data.decode("utf-8")

    def test_timer_requires_login(self, client):
        """未ログイン状態でタイマーページにアクセスするとリダイレクト"""
        response = client.get("/timer")
        assert response.status_code == 302  # リダイレクト

    def test_settings_requires_login(self, client):
        """未ログイン状態で設定ページにアクセスするとリダイレクト"""
        response = client.get("/settings")
        assert response.status_code == 302

    def test_history_requires_login(self, client):
        """未ログイン状態で履歴ページにアクセスするとリダイレクト"""
        response = client.get("/history")
        assert response.status_code == 302


# ============================================================
# 設定のテスト
# ============================================================

class TestSettings:
    """設定ページのテスト"""

    def test_settings_page_loads(self, logged_in_client):
        """設定ページが正常に表示される"""
        response = logged_in_client.get("/settings")
        assert response.status_code == 200
        assert "設定" in response.data.decode("utf-8")

    def test_update_settings_success(self, app, logged_in_client):
        """設定の更新が正常に保存される"""
        response = logged_in_client.post("/settings", data={
            "work_duration": "30",
            "short_break": "10",
            "long_break": "20",
            "sessions_before_long_break": "3",
        }, follow_redirects=True)
        assert response.status_code == 200

        # データベースに保存された設定を確認
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            assert user.work_duration == 30
            assert user.short_break == 10
            assert user.long_break == 20
            assert user.sessions_before_long_break == 3

    def test_update_settings_invalid_value(self, logged_in_client):
        """無効な値での設定更新はエラー"""
        response = logged_in_client.post("/settings", data={
            "work_duration": "999",  # 範囲外（max: 120）
            "short_break": "5",
            "long_break": "15",
            "sessions_before_long_break": "4",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "範囲" in response.data.decode("utf-8")

    def test_update_settings_non_numeric(self, logged_in_client):
        """数値以外の入力はエラー"""
        response = logged_in_client.post("/settings", data={
            "work_duration": "abc",
            "short_break": "5",
            "long_break": "15",
            "sessions_before_long_break": "4",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "正しくありません" in response.data.decode("utf-8")


# ============================================================
# APIセッション記録のテスト
# ============================================================

class TestSessionAPI:
    """セッション記録APIのテスト"""

    def test_record_work_session(self, app, logged_in_client):
        """作業セッションの記録"""
        response = logged_in_client.post("/api/session",
            json={"session_type": "work", "duration_minutes": 25},
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data

        # データベースに保存されている
        with app.app_context():
            session = db.session.get(PomodoroSession, data["id"])
            assert session is not None
            assert session.session_type == "work"
            assert session.duration_minutes == 25

    def test_record_break_session(self, app, logged_in_client):
        """休憩セッションの記録"""
        response = logged_in_client.post("/api/session",
            json={"session_type": "break", "duration_minutes": 5},
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_record_session_invalid_type(self, logged_in_client):
        """無効なsession_typeはエラー"""
        response = logged_in_client.post("/api/session",
            json={"session_type": "invalid", "duration_minutes": 25},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_record_session_invalid_duration(self, logged_in_client):
        """無効なduration_minutesはエラー"""
        response = logged_in_client.post("/api/session",
            json={"session_type": "work", "duration_minutes": -5},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_record_session_requires_login(self, client):
        """未ログインでのAPI呼び出しはリダイレクト"""
        response = client.post("/api/session",
            json={"session_type": "work", "duration_minutes": 25},
            content_type="application/json",
        )
        assert response.status_code == 302

    def test_record_session_no_json(self, logged_in_client):
        """JSONなしのリクエストはエラー"""
        response = logged_in_client.post("/api/session",
            data="not json",
            content_type="text/plain",
        )
        assert response.status_code == 400


# ============================================================
# 履歴ページのテスト
# ============================================================

class TestHistory:
    """履歴ページのテスト"""

    def test_history_page_loads(self, logged_in_client):
        """履歴ページが正常に表示される"""
        response = logged_in_client.get("/history")
        assert response.status_code == 200
        assert "履歴" in response.data.decode("utf-8")

    def test_history_shows_sessions(self, app, logged_in_client):
        """記録したセッションが履歴ページに表示される"""
        # セッションを記録
        logged_in_client.post("/api/session",
            json={"session_type": "work", "duration_minutes": 25},
            content_type="application/json",
        )
        logged_in_client.post("/api/session",
            json={"session_type": "break", "duration_minutes": 5},
            content_type="application/json",
        )

        # 履歴ページを確認
        response = logged_in_client.get("/history")
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        assert "25" in body  # 作業時間25分が表示
        assert "5" in body   # 休憩時間5分が表示

    def test_history_shows_statistics(self, logged_in_client):
        """統計情報が正しく表示される"""
        # 複数のセッションを記録
        for _ in range(3):
            logged_in_client.post("/api/session",
                json={"session_type": "work", "duration_minutes": 25},
                content_type="application/json",
            )

        response = logged_in_client.get("/history")
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        # 合計作業時間（25分×3=75分）が含まれている
        assert "75" in body

    def test_history_empty_state(self, logged_in_client):
        """セッションがない場合の空状態表示"""
        response = logged_in_client.get("/history")
        assert response.status_code == 200
        assert "まだセッション" in response.data.decode("utf-8")

    def test_history_only_shows_own_sessions(self, app, client):
        """他のユーザーのセッションは表示されない"""
        # ユーザー1を登録・ログインしてセッション記録
        client.post("/register", data={
            "username": "user1", "password": "pass1234", "confirm_password": "pass1234"
        })
        client.post("/login", data={"username": "user1", "password": "pass1234"})
        client.post("/api/session",
            json={"session_type": "work", "duration_minutes": 25},
            content_type="application/json",
        )
        client.get("/logout")

        # ユーザー2を登録・ログインして履歴を確認
        client.post("/register", data={
            "username": "user2", "password": "pass5678", "confirm_password": "pass5678"
        })
        client.post("/login", data={"username": "user2", "password": "pass5678"})
        response = client.get("/history")
        body = response.data.decode("utf-8")
        # ユーザー2には作業セッションがないので、空状態が表示される
        assert "まだセッション" in body
