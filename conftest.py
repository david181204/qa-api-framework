import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def token(base_url):
    r = requests.post(f"{base_url}/login", json={"username": "david", "password": "123456"})
    assert r.status_code == 200
    return r.json()["token"]