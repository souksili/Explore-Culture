import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_hello_world(client):
    """Teste la route principale '/'"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Hello, World!" in response.data

def test_api(client):
    """Teste la route '/api'"""
    response = client.get('/api')
    assert response.status_code == 200
    assert b"Bienvenue dans l'API de Explore Culture" in response.data