import pytest
from app import app as flask_app, timer


@pytest.fixture(autouse=True)
def reset_timer():
    """Reset the global timer before each test."""
    timer.reset()
    yield
    timer.reset()


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200


def test_get_status(client):
    response = client.get('/api/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'is_running' in data
    assert 'is_break' in data
    assert 'time_remaining' in data
    assert 'cycle_count' in data


def test_start_timer(client):
    response = client.post('/api/start')
    assert response.status_code == 200
    data = response.get_json()
    assert 'is_running' in data


def test_stop_timer(client):
    response = client.post('/api/stop')
    assert response.status_code == 200
    data = response.get_json()
    assert 'is_running' in data


def test_reset_timer(client):
    response = client.post('/api/reset')
    assert response.status_code == 200
    data = response.get_json()
    assert 'is_running' in data


def test_timer_state_after_start(client):
    response = client.post('/api/start')
    data = response.get_json()
    assert data['is_running'] is True


def test_timer_state_after_stop(client):
    client.post('/api/start')
    response = client.post('/api/stop')
    data = response.get_json()
    assert data['is_running'] is False


def test_timer_state_after_reset(client):
    from app import timer as t
    client.post('/api/start')
    response = client.post('/api/reset')
    data = response.get_json()
    assert data['time_remaining'] == t.work_duration
