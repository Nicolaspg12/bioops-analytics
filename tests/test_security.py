import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path/'security.db'), base_url='http://localhost:8001')


@pytest.mark.parametrize('origin', ['https://example.invalid', 'null', 'http://localhost:8002'])
def test_external_origin_cannot_write(client, origin):
    assert client.post('/api/demo', headers={'Origin': origin}).status_code == 403
    assert client.get('/api/dashboard').json()['metrics']['total'] == 0


def test_same_origin_and_command_line_still_work(client):
    assert client.post('/api/demo', headers={'Origin': 'http://localhost:8001'}).status_code == 200
    assert client.get('/api/health').status_code == 200


@pytest.mark.parametrize('host', ['example.invalid', 'localhost.example.invalid', 'localhost@evil.invalid', 'localhost:bad'])
def test_untrusted_host_is_rejected(client, host):
    assert client.get('/api/dashboard', headers={'Host': host}).status_code == 400


def test_cross_site_and_framing_are_blocked(client):
    assert client.get('/api/export', headers={'Sec-Fetch-Site':'cross-site'}).status_code == 403
    response = client.get('/')
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert "script-src 'self'" in response.headers['Content-Security-Policy']
