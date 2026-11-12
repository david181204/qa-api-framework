import requests

def test_login_success(base_url):
    r = requests.post(f"{base_url}/login", json={"username": "david", "password": "123456"})
    assert r.status_code == 200
    assert "token" in r.json()

def test_login_wrong_password(base_url):
    r = requests.post(f"{base_url}/login", json={"username": "david", "password": "wrong"})
    assert r.status_code == 401

def test_login_missing_field(base_url):
    r = requests.post(f"{base_url}/login", json={"username": "david"})
    assert r.status_code == 422

def test_login_empty_password(base_url):
    r = requests.post(f"{base_url}/login", json={"username": "david", "password": ""})
    assert r.status_code == 401